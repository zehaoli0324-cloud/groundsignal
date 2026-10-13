"""Local-only browser UI for the GroundSignal collector. No web framework required."""
import argparse
import copy
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import threading
from urllib.parse import parse_qs, urlencode, urlparse
import webbrowser

import requests
from collect import ROOT, atomic_write, collect, validate_name
from search_sources import SearchFailure
from runtime_paths import CONFIG_PATH, VERSION
from vault_connection import check_vault, choose_folder, discover, installed

CONFIG = CONFIG_PATH
PAGE = ROOT / 'templates/collector.html'


def obsidian_uri(path):
    return 'obsidian://open?' + urlencode({'path': str(path.resolve())})


class App:
    def __init__(self, config_path=CONFIG, collector=collect):
        self.config_path = Path(config_path)
        self.collector = collector
        self.lock = threading.RLock()
        self.token = secrets.token_urlsafe(32)
        self.job = None
        self.config = (json.loads(self.config_path.read_text(encoding='utf-8-sig'))
                       if self.config_path.exists() else {'vault': '', 'max_results': 6})
        self.obsidian_installed = installed()

    def vault(self):
        value = self.config.get('vault')
        if not value:
            raise ValueError('请先连接 Obsidian 笔记库')
        return Path(value).resolve()

    def settings(self):
        value = self.config.get('vault', '')
        path = Path(value) if value else None
        exists = bool(path and path.is_dir())
        is_vault = bool(exists and (path / '.obsidian').is_dir())
        return {'vault': str(path.resolve()) if path else '', 'exists': exists,
                'connected': is_vault, 'obsidian_installed': self.obsidian_installed,
                'name': path.name if path else '',
                'max_results': self.config.get('max_results', 6)}

    def history(self):
        if not self.settings()['connected']:
            return []
        directory = self.vault() / '09-采集记录'
        entries = []
        paths = sorted(directory.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
        seen = set()
        for path in paths:
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
                name = validate_name(data['query'])
                if name in seen:
                    continue
                seen.add(name)
                entries.append(self.summary(path.stem, data))
                if len(entries) >= 40:
                    break
            except (ValueError, KeyError, TypeError, OSError):
                continue
        return entries

    def summary(self, report_id, data):
        results = data.get('results', [])
        return {'id': report_id, 'query': data['query'], 'time': data.get('retrieved_at', ''),
                'count': len(results), 'pages': sum(x.get('status') == 'page_fetched' for x in results),
                'note_uri': obsidian_uri(self.vault() / '01-公司' / (data['query'] + '.md')),
                'report_uri': obsidian_uri(self.vault() / '09-采集记录' / (report_id + '.md'))}

    def detail(self, report_id):
        if not report_id or Path(report_id).name != report_id or any(c in report_id for c in '/\\:'):
            raise ValueError('无效的采集记录')
        directory = (self.vault() / '09-采集记录').resolve()
        path = (directory / (report_id + '.json')).resolve()
        if path.parent != directory:
            raise ValueError('无效的采集记录')
        data = json.loads(path.read_text(encoding='utf-8'))
        validate_name(data['query'])
        return dict(self.summary(report_id, data), results=data['results'], search=data.get('search'))

    def update_settings(self, data):
        with self.lock:
            if self.job and self.job['status'] == 'running':
                raise ValueError('正在采集，请完成后再修改保存位置')
            limit = data.get('max_results', 6)
            if type(limit) is not int or not 1 <= limit <= 10:
                raise ValueError('来源数量应为 1 到 10')
            connection = check_vault(data.get('vault', ''), write_test=True)
            updated = dict(self.config, vault=connection['vault'], max_results=limit)
            atomic_write(self.config_path, json.dumps(updated, ensure_ascii=False, indent=2))
            self.config = updated
            self.job = None

    def start(self, name):
        if not isinstance(name, str):
            raise ValueError('请输入公司名称')
        name = validate_name(name.strip())
        with self.lock:
            if self.job and self.job['status'] == 'running':
                raise ValueError('已有采集任务正在运行，请稍候')
            if not self.settings()['connected']:
                raise ValueError('请先连接有效的 Obsidian 笔记库')
            self.job = {'query': name, 'status': 'running', 'stage': 'searching',
                        'message': '准备搜索公开资料', 'current': 0, 'total': 0}
            threading.Thread(target=self.run, args=(name, self.vault(), self.config.get('max_results', 6)),
                             daemon=True).start()

    def companies(self):
        if not self.settings()['connected']:
            return []
        names = []
        for path in (self.vault() / '01-公司').glob('*.md'):
            if path.is_symlink() or not path.is_file():
                continue
            try:
                names.append(validate_name(path.stem))
            except ValueError:
                continue
        return sorted(set(names), key=str.casefold)

    def start_update(self, names=None, all_companies=False, retry_failed=False):
        with self.lock:
            if self.job and self.job['status'] == 'running':
                raise ValueError('已有任务正在运行，请等待完成或停止剩余更新')
            if not self.settings()['connected']:
                raise ValueError('请先连接有效的 Obsidian 笔记库')
            inventory = self.companies()
            if retry_failed:
                if not self.job or self.job.get('kind') != 'batch':
                    raise ValueError('没有可重试的更新任务')
                names = [item['name'] for item in self.job['items'] if item['status'] == 'error']
            elif all_companies:
                names = inventory
            if not isinstance(names, list) or not names or any(not isinstance(n, str) for n in names):
                raise ValueError('请选择至少一家公司；新公司请先通过搜索添加')
            names = list(dict.fromkeys(names))
            if any(n not in inventory for n in names):
                raise ValueError('部分公司已不在当前笔记库中，请刷新列表后重试')
            self.job = {'kind': 'batch', 'query': '公司资料更新', 'status': 'running', 'stage': 'searching',
                        'message': '正在准备更新队列', 'current': 0, 'total': 0,
                        'completed': 0, 'succeeded': 0, 'failed': 0, 'cancel_requested': False,
                        'items': [{'name': n, 'status': 'queued'} for n in names]}
            threading.Thread(target=self.run_update, args=(self.vault(), self.config.get('max_results', 6)), daemon=True).start()

    def cancel_update(self):
        with self.lock:
            if not self.job or self.job.get('kind') != 'batch' or self.job['status'] != 'running':
                raise ValueError('当前没有正在进行的更新队列')
            self.job['cancel_requested'] = True
            self.job['message'] = '已请求停止；当前公司处理完毕后，不再开始下一家公司'

    def run_update(self, vault, limit):
        items = self.job['items']
        for index, item in enumerate(items):
            with self.lock:
                if self.job['cancel_requested']:
                    for pending in items[index:]:
                        pending['status'] = 'skipped'
                    break
                item['status'] = 'running'
                self.job.update(active_company=item['name'], active_index=index + 1)
            def progress(stage, message, current=0, total=0):
                with self.lock:
                    self.job.update(stage=stage, current=current, total=total)
                    if not self.job['cancel_requested']:
                        self.job['message'] = f'{index + 1}/{len(items)} · {item["name"]} · {message}'
            try:
                result = self.collector(item['name'], vault, limit, progress=progress, force_refresh=True)
                with self.lock:
                    item.update(status='done', result=result, report_id=Path(result['report']).stem,
                                message='已更新' if result.get('changed', True) else '已检查，内容未变化')
                    self.job['succeeded'] += 1
            except Exception as exc:
                with self.lock:
                    message = '网络连接失败，请稍后重试' if isinstance(exc, requests.RequestException) else str(exc)
                    item.update(status='error', message=message[:500], diagnostics=getattr(exc, 'diagnostics', []))
                    self.job['failed'] += 1
            finally:
                with self.lock:
                    self.job['completed'] += 1
        with self.lock:
            cancelled = any(item['status'] == 'skipped' for item in items)
            status = 'cancelled' if cancelled else ('partial' if self.job['failed'] else 'done')
            self.job.update(status=status, stage='done', active_company='',
                            message=f'已处理 {self.job["completed"]}/{len(items)} 家：成功 {self.job["succeeded"]} 家，失败 {self.job["failed"]} 家。'
                                    + ('剩余公司已停止。' if cancelled else ''),
                            finished_at=datetime.now(timezone(timedelta(hours=8))).isoformat())

    def run(self, name, vault, limit):
        def progress(stage, message, current=0, total=0):
            with self.lock:
                self.job.update(stage=stage, message=message, current=current, total=total)
        try:
            result = self.collector(name, vault, limit, progress=progress)
            with self.lock:
                search_meta = result.get('search', {})
                suffix = (' · 搜索来源：' + search_meta['provider']) if search_meta.get('provider') else ''
                if search_meta.get('cached'):
                    suffix += '（搜索缓存）'
                self.job.update(status='done', stage='done', message='采集完成，已写入 Obsidian' + suffix,
                                result=result, report_id=Path(result['report']).stem,
                                finished_at=datetime.now(timezone(timedelta(hours=8))).isoformat())
        except Exception as exc:
            if isinstance(exc, SearchFailure):
                message = str(exc)
            elif isinstance(exc, requests.RequestException):
                message = '暂时无法连接搜索服务，请检查网络，稍后再试。'
            elif isinstance(exc, RuntimeError):
                message = '搜索服务暂时没有返回可用结果，可能受到访问限制，也可能名称不够准确。请稍后重试，或输入公司全称。'
            elif isinstance(exc, PermissionError):
                message = '无法写入仓库，请检查文件夹权限或文件是否被占用。'
            else:
                message = str(exc)
            with self.lock:
                self.job.update(status='error', stage='error', message=message,
                                detail=str(exc)[:500], diagnostics=getattr(exc, 'diagnostics', []))

    def state(self):
        with self.lock:
            return {'app': 'GroundSignal', 'version': VERSION, 'config_id': str(self.config_path.resolve()),
                    'settings': self.settings(), 'job': copy.deepcopy(self.job), 'company_count': len(self.companies()),
                    'history': self.history()}


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, status, data, content_type='application/json; charset=utf-8'):
            body = (json.dumps(data, ensure_ascii=False) if not isinstance(data, str) else data).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.end_headers()
            self.wfile.write(body)

        def local_request(self):
            expected = f'127.0.0.1:{self.server.server_port}'
            return self.headers.get('Host') == expected and self.headers.get('Origin', 'http://' + expected) == 'http://' + expected

        def do_GET(self):
            if not self.local_request():
                return self.send(403, {'error': '仅允许本机界面访问'})
            parsed = urlparse(self.path)
            try:
                if parsed.path == '/':
                    return self.send(200, PAGE.read_text(encoding='utf-8').replace('__TOKEN__', app.token), 'text/html; charset=utf-8')
                if parsed.path == '/api/state':
                    return self.send(200, app.state())
                if parsed.path == '/api/vaults':
                    return self.send(200, {'vaults': discover(), 'obsidian_installed': app.obsidian_installed})
                if parsed.path == '/api/companies':
                    return self.send(200, {'companies': app.companies()})
                if parsed.path == '/api/report':
                    return self.send(200, app.detail(parse_qs(parsed.query).get('id', [''])[0]))
                return self.send(404, {'error': '页面不存在'})
            except (ValueError, KeyError, OSError) as exc:
                return self.send(400, {'error': str(exc)})

        def do_POST(self):
            if not self.local_request() or self.headers.get('X-GroundSignal-Token') != app.token:
                return self.send(403, {'error': '页面已过期，请刷新后重试'})
            try:
                length = int(self.headers.get('Content-Length', 0))
                if not 0 < length <= 65536:
                    raise ValueError('请求内容过长或为空')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError('请求格式错误')
                if self.path == '/api/collect':
                    app.start(data.get('name'))
                elif self.path == '/api/update':
                    app.start_update(names=data.get('names'), all_companies=data.get('all') is True)
                elif self.path == '/api/update-cancel':
                    app.cancel_update()
                elif self.path == '/api/update-retry':
                    app.start_update(retry_failed=True)
                elif self.path == '/api/pick-vault':
                    return self.send(200, {'path': choose_folder(app.config.get('vault', ''))})
                elif self.path == '/api/check-vault':
                    return self.send(200, check_vault(data.get('vault'), write_test=True))
                elif self.path == '/api/open-obsidian':
                    if not app.obsidian_installed:
                        raise ValueError('未检测到 Obsidian，请先安装桌面版')
                    uri = 'obsidian://open?' + urlencode({'vault': str(app.vault())}) if app.settings()['connected'] and not data.get('choose') else 'obsidian://choose-vault'
                    os.startfile(uri)
                elif self.path == '/api/disconnect':
                    with app.lock:
                        if app.job and app.job['status'] == 'running':
                            raise ValueError('正在采集，请完成后再断开')
                        app.config = dict(app.config, vault='')
                        atomic_write(app.config_path, json.dumps(app.config, ensure_ascii=False, indent=2))
                        app.job = None
                elif self.path == '/api/settings':
                    app.update_settings(data)
                elif self.path == '/api/folder':
                    if not app.vault().is_dir():
                        raise ValueError('仓库文件夹不存在')
                    os.startfile(str(app.vault()))
                elif self.path == '/api/shutdown':
                    with app.lock:
                        if app.job and app.job['status'] == 'running':
                            raise ValueError('正在采集，请完成后再退出')
                    self.send(200, {'ok': True})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                else:
                    return self.send(404, {'error': '接口不存在'})
                return self.send(200, {'ok': True})
            except (ValueError, KeyError, OSError) as exc:
                return self.send(400, {'error': str(exc)})
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    app = App()
    # Reuse this project's running instance when the launcher is double-clicked twice.
    url = f'http://127.0.0.1:{args.port}'
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), make_handler(app))
    except OSError:
        session = requests.Session()
        session.trust_env = False
        try:
            response = session.get(url + '/api/state', timeout=2)
            state = response.json()
            if response.ok and state.get('app') == 'GroundSignal' and state.get('config_id') == str(app.config_path.resolve()) and state.get('version') == VERSION:
                if not args.no_browser:
                    webbrowser.open(url)
                return
        except (requests.RequestException, ValueError):
            pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(app))
        url = f'http://127.0.0.1:{server.server_port}'
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
