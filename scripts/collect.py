#!/usr/bin/env python3
"""Search company names, fetch public pages, and save attributable leads to a vault.

No model/API key required. Search results are leads, never verified relationships.
"""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from search_sources import search
from runtime_paths import RESOURCE_DIR, CONFIG_PATH

ROOT = RESOURCE_DIR
START = '<!-- groundsignal:collection:start -->'
END = '<!-- groundsignal:collection:end -->'


def validate_name(name):
    if (not name or len(name) > 100 or name != name.strip()
            or re.search(r'[<>:"/\\|?*\[\]#\x00-\x1f]', name)
            or name.endswith('.') or name in {'.', '..'}
            or re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', name)):
        raise ValueError('请输入公司名称，不要输入路径或特殊字符')
    return name


def fetch(session, url, **kwargs):
    response = session.get(url, timeout=(10, 20), **kwargs)
    response.raise_for_status()
    if not response.encoding or response.encoding.lower() == 'iso-8859-1':
        response.encoding = response.apparent_encoding
    return response


def enrich(session, item, name):
    result = dict(item, status='search_only', excerpt='')
    try:
        response = fetch(session, item['url'])
        if 'html' not in response.headers.get('Content-Type', '').lower():
            raise ValueError('非 HTML 来源，仅保留搜索线索')
        soup = BeautifulSoup(response.text, 'html.parser')
        for node in soup(['head', 'script', 'style', 'nav', 'footer', 'header']):
            node.decompose()
        lines = [re.sub(r'\s+', ' ', x).strip() for x in soup.get_text('\n').splitlines()]
        matches = [x for x in lines if name in x and len(x) >= 40
                   and re.search(r'[，。；：,;]', x)]
        if not matches:
            raise ValueError('未取得包含公司名的正文，可能需要登录或动态加载')
        result.update(status='page_fetched', excerpt='\n'.join(dict.fromkeys(matches))[:1200],
                      resolved_url=response.url)
    except (requests.RequestException, ValueError) as exc:
        result['error'] = str(exc)[:300]
    return result


def quote(text):
    # External text stays a quotation and cannot create fabricated wikilinks/HTML.
    text = text.replace('<', '&lt;').replace('>', '&gt;').replace('[', '［').replace(']', '］')
    return '\n'.join('> ' + line for line in text.splitlines())


def atomic_write(path, text):
    import os
    import tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(text)
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def save(vault, name, search_url, results, search_info=None):
    now = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
    note = vault / '01-公司' / (name + '.md')
    existing = note.read_text(encoding='utf-8') if note.exists() else (
        '---\ntype: company\ntags: [type/company]\nname: ' + json.dumps(name, ensure_ascii=False)
        + '\nevidence: UNKNOWN\nidentity_status: UNCONFIRMED\n---\n\n# ' + name + '\n')
    if existing.count(START) != existing.count(END) or existing.count(START) > 1:
        raise ValueError('自动采集区标记损坏，停止写入以保护笔记')
    if START in existing and existing.index(END) < existing.index(START):
        raise ValueError('自动采集区标记顺序错误')
    digest = hashlib.sha256(json.dumps(results, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    report_name = f'{name}-{digest}'
    report = vault / '09-采集记录' / (report_name + '.md')
    body = [f'# {name}：自动搜索采集', '', f'采集时间：{now}', f'公司：[[01-公司/{name}]]',
            f'搜索入口：{search_url}', '',
            '以下为自动抓取的来源线索，未完成主体身份确认或事实核验，不自动生成投资、供应或竞争关系。', '']
    if search_info:
        body += [f'搜索服务：{search_info["provider"]}；使用搜索缓存：{search_info["cached"]}',
                 f'搜索结果取得时间：{search_info["searched_at"]}', '']
    for item in results:
        body += ['## ' + item['title'].replace('\n', ' '), '', '来源：' + item['url'],
                 '抓取状态：' + item['status'], '', '搜索摘要：', quote(item['snippet']), '']
        if item['excerpt']:
            body += ['网页摘录：', quote(item['excerpt']), '']
        if item.get('error'):
            body += ['抓取说明：' + item['error'], '']
    if not report.exists():
        atomic_write(report, '\n'.join(body))
    raw = report.with_suffix('.json')
    if not raw.exists():
        atomic_write(raw, json.dumps({'query': name, 'retrieved_at': now, 'search_url': search_url,
                                     'results': results, 'search': search_info}, ensure_ascii=False, indent=2))
    block = '\n'.join([START, '## 自动采集（待核实）', '', f'最近检索：{now}',
                      f'本次取得 {len(results)} 条搜索线索，{sum(x["status"] == "page_fetched" for x in results)} 个网页摘录。',
                      f'查看来源与摘录：[[09-采集记录/{report_name}]]',
                      '名称匹配不代表主体已确认；搜索线索不代表关系成立。', END])
    if START in existing:
        before, tail = existing.split(START)
        _, after = tail.split(END)
        updated = before + block + after
    else:
        updated = existing.rstrip() + '\n\n' + block + '\n'
    atomic_write(note, updated)
    return note, report


def collect(name, vault, limit=6, dry_run=False, progress=None, force_refresh=False):
    def notify(stage, message, current=0, total=0):
        if progress:
            progress(stage, message, current, total)

    validate_name(name)
    vault = Path(vault).resolve()
    if not vault.is_dir():
        raise ValueError(f'仓库目录不存在：{vault}')
    with requests.Session() as session:
        session.headers['User-Agent'] = 'Mozilla/5.0 (compatible; GroundSignal/1.0)'
        notify('searching', f'正在搜索「{name}」的公开资料')
        search_info = search(session, name, limit, progress=progress, force_refresh=force_refresh)
        search_url, items = search_info['search_url'], search_info['items']
        results = []
        for index, item in enumerate(items):
            notify('fetching', f'正在读取来源 {index + 1}/{len(items)}：{item["title"]}', index, len(items))
            results.append(enrich(session, item, name))
    if dry_run:
        return {'query': name, 'results': results, 'search': {k: v for k, v in search_info.items() if k != 'items'}}
    notify('saving', '正在保存公司笔记和来源记录', len(results), len(results))
    search_meta = {k: v for k, v in search_info.items() if k != 'items'}
    digest = hashlib.sha256(json.dumps(results, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    current_note = vault / '01-公司' / (name + '.md')
    changed = not current_note.exists() or f'09-采集记录/{name}-{digest}' not in current_note.read_text(encoding='utf-8')
    note, report = save(vault, name, search_url, results, search_meta)
    return {'query': name, 'note': str(note), 'report': str(report),
            'changed': changed,
            'search': search_meta, 'search_results': len(results),
            'pages_fetched': sum(x['status'] == 'page_fetched' for x in results)}


def main():
    parser = argparse.ArgumentParser(description='联网搜索公司并自动采集到 Obsidian')
    parser.add_argument('companies', nargs='+', help='一个或多个公司名称')
    parser.add_argument('--config', type=Path, default=CONFIG_PATH)
    parser.add_argument('--vault', type=Path)
    parser.add_argument('--max-results', type=int, choices=range(1, 11))
    parser.add_argument('--dry-run', action='store_true', help='联网检索但不写入')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8-sig')) if args.config.exists() else {}
    vault = args.vault or config.get('vault')
    if not vault:
        parser.error('请用 --vault 指定仓库，或配置 collector-config.json')
    limit = args.max_results or config.get('max_results', 6)
    if not isinstance(limit, int) or not 1 <= limit <= 10:
        parser.error('max_results 必须是 1 到 10')
    failed = False
    for name in args.companies:
        try:
            print(json.dumps(collect(name, vault, limit, args.dry_run), ensure_ascii=False, indent=2))
        except (ValueError, RuntimeError, OSError, requests.RequestException) as exc:
            failed = True
            print(f'{name} 采集失败：{exc}', file=sys.stderr)
    return 1 if failed else 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    sys.exit(main())
