"""Independent search providers, explicit diagnostics and persistent backoff/cache.

Challenge pages are detected, never solved. A blocked provider is paused while
another independent provider is tried. Results must still match the company name.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import re
import threading
import time
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import requests
from runtime_paths import CACHE_DIR

CACHE_TTL = 6 * 3600
COOLDOWN = 30 * 60
INTERVAL = 5
LOCK = threading.Lock()
LABELS = {'sogou': '搜狗', 'so360': '360', 'brave_api': 'Brave API'}


class SearchFailure(RuntimeError):
    def __init__(self, code, message, diagnostics=None, retry_after=0):
        super().__init__(message)
        self.code = code
        self.diagnostics = diagnostics or []
        self.retry_after = retry_after


def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def write_json(path, value):
    import tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def normalize(text):
    return re.sub(r'\s+', '', text).casefold()


def valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ('https', 'http') and bool(parsed.hostname)


def add_result(items, seen, name, title, snippet, url, provider):
    if not valid_url(url) or normalize(name) not in normalize(title + snippet) or url in seen:
        return
    seen.add(url)
    items.append({'title': title.strip(), 'snippet': snippet.strip()[:600], 'url': url,
                  'search_provider': provider})


def detect_challenge(soup):
    title = soup.title.get_text(' ', strip=True) if soup.title else ''
    text = soup.get_text(' ', strip=True)
    if (any(x in title for x in ['访问异常', '验证码', '安全验证', '访问过于频繁'])
            or soup.select_one('form#challenge-form, form#captcha-form')
            or ('请输入验证码以便正常访问' in text)
            or ('请开启JavaScript' in text and len(text) < 1000)):
        raise SearchFailure('blocked', '搜索服务要求安全验证，已暂停该搜索源', retry_after=COOLDOWN)


def parse_360(html, name, limit):
    soup = BeautifulSoup(html, 'html.parser')
    detect_challenge(soup)
    anchors = soup.select('h3.res-title a')
    items, seen = [], set()
    for a in anchors:
        container = a.find_parent('li')
        node = container.select_one('.res-list-summary') if container else None
        add_result(items, seen, name, a.get_text('', strip=True),
                   node.get_text('', strip=True) if node else '',
                   a.get('data-mdurl') or a.get('data-cache') or '', '360')
    return parsed_result(items, anchors, soup, limit)


def parse_sogou(html, name, limit):
    soup = BeautifulSoup(html, 'html.parser')
    detect_challenge(soup)
    headings = soup.select('.results h3, h3.pt, h3.vr-title')
    items, seen = [], set()
    for heading in headings:
        a = heading.find('a') or heading.find_parent('a')
        if not a:
            continue
        if urlparse(urljoin('https://www.sogou.com', a.get('href', ''))).hostname in {'apis.map.qq.com', 'map.qq.com'}:
            continue
        container = heading.find_parent('div', class_=lambda c: c and ('vrwrap' in c.split() or 'rb' in c.split()))
        if not container:
            continue
        snippet_node = container.select_one('.ft, .star-wiki, .fz-mid.space-txt, .str_info, .str-text-info')
        snippet = snippet_node.get_text('', strip=True) if snippet_node else ''
        title = heading.get_text('', strip=True)
        citation = container.select_one('a.citeLinkClass')
        url = citation.get('href', '') if citation else a.get('href', '')
        # Direct target from this result is preferable to the search redirect.
        direct = container.select_one('.r-sech[data-url]')
        if direct and valid_url(direct.get('data-url', '')):
            url = direct['data-url']
        url = urljoin('https://www.sogou.com', url)
        if urlparse(url).hostname in {'apis.map.qq.com', 'map.qq.com'}:
            continue
        add_result(items, seen, name, title, snippet, url, '搜狗')
    return parsed_result(items, headings, soup, limit)


def parsed_result(items, nodes, soup, limit):
    if items:
        return items[:limit]
    text = soup.get_text('', strip=True)
    if nodes or any(x in text for x in ['没有找到', '未找到相关', '抱歉，未找到']):
        raise SearchFailure('no_match', '未找到名称匹配的结果')
    raise SearchFailure('parse_error', '返回页面中没有可识别的搜索结果，可能是页面结构变化')


def get_response(session, provider, name):
    if provider == 'brave_api':
        response = session.get('https://api.search.brave.com/res/v1/web/search',
                               params={'q': name + ' 公司', 'count': 10, 'search_lang': 'zh-hans'},
                               headers={'X-Subscription-Token': os.environ['BRAVE_SEARCH_API_KEY']},
                               timeout=(10, 20))
    else:
        url, key = ('https://www.sogou.com/web', 'query') if provider == 'sogou' else ('https://www.so.com/s', 'q')
        response = session.get(url, params={key: name + ' 公司'}, timeout=(10, 20))
    if response.status_code in (401, 402, 403, 429):
        try:
            retry_after = max(COOLDOWN, int(response.headers.get('Retry-After', COOLDOWN)))
        except ValueError:
            retry_after = COOLDOWN
        code = 'configuration' if provider == 'brave_api' and response.status_code in (401, 402) else 'blocked'
        raise SearchFailure(code, f'HTTP {response.status_code}：服务拒绝请求', retry_after=retry_after)
    response.raise_for_status()
    if not response.encoding or response.encoding.lower() == 'iso-8859-1':
        response.encoding = response.apparent_encoding
    return response


def search(session, name, limit, progress=None, cache_dir=None, providers=None, force_refresh=False):
    cache_dir = Path(cache_dir) if cache_dir is not None else CACHE_DIR
    providers = providers or (['brave_api'] if os.environ.get('BRAVE_SEARCH_API_KEY') else []) + ['sogou', 'so360']
    fingerprint = hashlib.sha256(json.dumps([name, limit, providers, 2], ensure_ascii=False).encode()).hexdigest()
    cache_path = cache_dir / ('search-' + fingerprint + '.json')
    diagnostics = []
    with LOCK:
        cached = read_json(cache_path, {})
        if not force_refresh and cached.get('expires_at', 0) > time.time() and cached.get('items'):
            if progress:
                progress('searching', '使用 6 小时内的搜索缓存，避免重复请求搜索网站', 0, 0)
            return dict(cached, cached=True, diagnostics=[])
        state_path = cache_dir / 'providers.json'
        state = read_json(state_path, {})
        for provider in providers:
            status = state.get(provider, {})
            label = LABELS[provider]
            if status.get('blocked_until', 0) > time.time():
                diagnostics.append({'provider': label, 'code': 'cooldown', 'message': '处于暂停期，未发送请求',
                                    'retry_at': status['blocked_until']})
                continue
            delay = INTERVAL - (time.time() - status.get('last_request', 0))
            if delay > 0:
                if progress:
                    progress('searching', f'为减少访问限制，等待 {int(delay)+1} 秒后使用{label}', 0, 0)
                time.sleep(delay)
            if progress:
                progress('searching', f'正在使用{label}搜索「{name}」', 0, 0)
            status['last_request'] = time.time()
            state[provider] = status
            write_json(state_path, state)
            try:
                response = get_response(session, provider, name)
                if provider == 'brave_api':
                    items, seen = [], set()
                    for row in response.json().get('web', {}).get('results', []):
                        add_result(items, seen, name, row.get('title', ''), row.get('description', ''), row.get('url', ''), label)
                    if not items:
                        raise SearchFailure('no_match', '未找到名称匹配的结果')
                    items = items[:limit]
                else:
                    items = (parse_sogou if provider == 'sogou' else parse_360)(response.text, name, limit)
                now = time.time()
                result = {'provider': label, 'search_url': response.url, 'items': items,
                          'searched_at': datetime.now(timezone.utc).isoformat(),
                          'expires_at': now + CACHE_TTL, 'cached': False, 'diagnostics': diagnostics}
                write_json(cache_path, result)
                return result
            except SearchFailure as exc:
                diagnostics.append({'provider': label, 'code': exc.code, 'message': str(exc)})
                if exc.retry_after:
                    status['blocked_until'] = time.time() + exc.retry_after
                    write_json(state_path, state)
            except (requests.RequestException, ValueError) as exc:
                # Avoid storing URLs, proxy credentials or API keys from exception text.
                diagnostics.append({'provider': label, 'code': 'network', 'message': type(exc).__name__})
        codes = {x['code'] for x in diagnostics}
        if codes == {'no_match'}:
            code, message = 'no_match', '各搜索源均未找到名称匹配的结果，请尝试公司全称。'
        elif codes & {'blocked', 'cooldown', 'configuration'}:
            code, message = 'unavailable', '当前可用搜索源未返回结果，部分服务要求验证或正在暂停。请稍后再试；持续受限时可配置正式搜索 API。'
        else:
            code, message = 'unavailable', '搜索源暂不可用，请检查网络或查看下方各搜索源的错误原因。'
        raise SearchFailure(code, message, diagnostics)
