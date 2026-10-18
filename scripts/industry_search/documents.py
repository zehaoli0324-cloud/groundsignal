"""Original-page snapshots with explicit failures, page locations and source hints."""
import io
import ipaddress
from pathlib import Path
import re
import socket
import time
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup
import requests

from .contracts import canonical_url, digest, domain_matches, hostname, mentions, now


class FetchError(RuntimeError):
    pass


def public_url(url):
    """Validate every redirect target before sending requests to public sources."""
    url = canonical_url(url)
    host = urlsplit(url).hostname
    try:
        addresses = socket.getaddrinfo(host, None)
    except OSError as exc:
        raise FetchError('dns_unavailable') from exc
    if not addresses or any(not ipaddress.ip_address(x[4][0]).is_global for x in addresses):
        raise FetchError('non_public_destination')
    return url


def source_hint(url, target, registry):
    host = hostname(url)
    if any(domain_matches(host, d) for d in target['official_domains']):
        return {'kind': 'company_site', 'tier_hint': 'T1', 'priority': 4,
                'note': 'First-party candidate; document identity and claim support require review'}
    for source in sorted(registry['sources'], key=lambda x: len(x['domain']), reverse=True):
        if domain_matches(host, source['domain']):
            return {k: source[k] for k in ('kind', 'tier_hint', 'priority')}
    return {'kind': 'unknown', 'tier_hint': 'UNKNOWN', 'priority': 1}


def parse_html(raw):
    soup = BeautifulSoup(raw, 'html.parser')
    title = soup.title.get_text(' ', strip=True) if soup.title else ''
    if (re.search(r'访问异常|安全验证|访问过于频繁|just a moment|access denied|verify you are human', title, re.I)
            or soup.select_one('form#challenge-form, form#captcha-form')
            or (len(soup.get_text()) < 2000 and re.search(r'请输入验证码|enable javascript and cookies', soup.get_text(), re.I))):
        raise FetchError('challenge_page')
    if soup.select_one('form input[type="password"]'):
        raise FetchError('authentication_required')
    published = soup.select_one('meta[property="article:published_time"], meta[name="date"], time[datetime]')
    published_hint = (published.get('content') or published.get('datetime')) if published else None
    for node in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
        node.decompose()
    main = soup.select_one('article') or soup.select_one('main') or soup.body or soup
    text = '\n'.join(x.strip() for x in main.get_text('\n').splitlines() if x.strip())
    return title, text, published_hint


def parse_pdf(raw, parser):
    if parser == 'docling':
        try:
            from docling.datamodel.base_models import DocumentStream
            from docling.document_converter import DocumentConverter
        except ImportError as exc:
            raise FetchError('docling_not_installed') from exc
        result = DocumentConverter().convert(DocumentStream(name='source.pdf', stream=io.BytesIO(raw)))
        # Markdown coordinates do not have a reliable page map in this adapter.
        text = result.document.export_to_markdown()
        return text, [], 'docling_markdown_page_mapping_not_available'
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise FetchError('pypdf_not_installed') from exc
    pages, parts, offset = [], [], 0
    for number, page in enumerate(PdfReader(io.BytesIO(raw)).pages, 1):
        text = page.extract_text() or ''
        pages.append({'page': number, 'start': offset, 'end': offset + len(text)})
        parts.append(text)
        offset += len(text) + 2
    return '\n\n'.join(parts), pages, 'pypdf_text_no_ocr'


class Fetcher:
    def __init__(self, budget, out, method='http', pdf_parser='pypdf', session=None):
        self.budget, self.out, self.method, self.pdf_parser = budget, Path(out), method, pdf_parser
        self.session = session or requests.Session()
        self.session.headers.update({'User-Agent': 'GroundSignalResearch/0.1 (public evidence collection)'})
        self.calls = 0
        self.robots = {}
        self.last_request = {}

    def _http(self, url, robots=True):
        deadline = time.monotonic() + self.budget['timeout_seconds']
        for _ in range(6):
            if time.monotonic() >= deadline:
                raise FetchError('fetch_timeout_budget')
            url = public_url(url)
            host = hostname(url)
            if robots and not self._allowed(url):
                raise FetchError('robots_disallowed_or_unavailable')
            if self.calls >= self.budget['max_fetch_calls']:
                raise FetchError('fetch_budget_exhausted')
            delay = self.budget['request_interval_seconds'] - (time.monotonic() - self.last_request.get(host, 0))
            if delay > 0:
                time.sleep(delay)
            self.last_request[host] = time.monotonic()
            self.calls += 1
            response = self.session.get(url, timeout=(5, self.budget['timeout_seconds']),
                                        allow_redirects=False, stream=True)
            try:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get('Location')
                    if not location:
                        raise FetchError('redirect_without_location')
                    url = urljoin(url, location)
                    continue
                raw = bytearray()
                for chunk in response.iter_content(65536):
                    if time.monotonic() >= deadline:
                        raise FetchError('fetch_timeout_budget')
                    raw.extend(chunk)
                    if len(raw) > self.budget['max_bytes']:
                        raise FetchError('response_too_large')
                return url, response.status_code, dict(response.headers), bytes(raw)
            finally:
                response.close()
        raise FetchError('too_many_redirects')

    def _allowed(self, url):
        parts = urlsplit(url)
        origin = parts.scheme + '://' + parts.netloc
        if origin not in self.robots:
            try:
                _, status, _, raw = self._http(origin + '/robots.txt', robots=False)
                if status == 404:
                    self.robots[origin] = True
                elif status == 200:
                    parser = RobotFileParser()
                    parser.parse(raw.decode('utf-8', errors='replace').splitlines())
                    self.robots[origin] = parser
                else:
                    self.robots[origin] = False
            except (requests.RequestException, FetchError, ValueError):
                self.robots[origin] = False
        policy = self.robots[origin]
        return policy if isinstance(policy, bool) else policy.can_fetch('GroundSignalResearch', url)

    def fetch(self, hit, target):
        url = hit['url']
        doc = {'id': 'doc_' + digest(url)[:20], 'url': url, 'resolved_url': url,
               'first_seen_at': hit['first_seen_at'], 'retrieved_at': now(),
               'status': 'FAILED', 'error_code': None, 'title': hit['title'],
               'text': '', 'pages': [], 'raw_sha256': None, 'text_sha256': None,
               'raw_path': None, 'parser': None, 'published_hint': None,
               'synthetic': False, 'fetcher': self.method}
        try:
            if self.method == 'crawl4ai':
                return self._crawl(doc, target)
            resolved, status, headers, raw = self._http(url)
            doc.update(resolved_url=resolved, http_status=status, retrieved_at=now(), raw_sha256=digest(raw))
            if status != 200:
                raise FetchError('http_' + str(status))
            path = self.out / 'sources' / (doc['id'] + '.bin')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            doc['raw_path'] = str(path.relative_to(self.out))
            content_type = headers.get('Content-Type', headers.get('content-type', '')).lower()
            if raw.startswith(b'%PDF-'):
                text, pages, parser = parse_pdf(raw, self.pdf_parser)
                doc.update(text=text, pages=pages, parser=parser)
            elif 'html' in content_type or b'<html' in raw[:1000].lower() or b'<!doctype html' in raw[:1000].lower():
                title, text, published_hint = parse_html(raw)
                doc.update(title=title or doc['title'], text=text, published_hint=published_hint,
                           parser='beautifulsoup_html')
            elif 'text/plain' in content_type:
                doc.update(text=raw.decode('utf-8'), parser='utf8_plain_text')
            else:
                raise FetchError('unsupported_content_type')
            self._finish(doc, target)
        except FetchError as exc:
            doc['error_code'] = str(exc)
        except (requests.RequestException, OSError, ValueError) as exc:
            doc['error_code'] = type(exc).__name__
        except Exception as exc:
            # Optional parsers may raise library-specific errors; no silent fallback.
            doc['error_code'] = 'parser_' + type(exc).__name__
        return doc

    def _finish(self, doc, target):
        doc['text_sha256'] = digest(doc['text'])
        if len(doc['text'].strip()) < 80:
            raise FetchError('insufficient_text_or_ocr_required')
        doc['status'] = 'FETCHED' if mentions(doc['text'], target) else 'IRRELEVANT'

    def _crawl(self, doc, target):
        try:
            import asyncio
            from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
        except ImportError as exc:
            raise FetchError('crawl4ai_not_installed') from exc
        public_url(doc['url'])
        if not any(domain_matches(hostname(doc['url']), domain) for domain in target['official_domains']):
            raise FetchError('browser_requires_explicit_official_domain')
        if not self._allowed(doc['url']):
            raise FetchError('robots_disallowed_or_unavailable')
        if self.calls >= self.budget['max_fetch_calls']:
            raise FetchError('fetch_budget_exhausted')
        self.calls += 1

        async def execute():
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                return await crawler.arun(url=doc['url'], config=CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS, page_timeout=self.budget['timeout_seconds'] * 1000,
                    check_robots_txt=True))

        result = asyncio.run(execute())
        if not result.success:
            raise FetchError('crawl4ai_fetch_failed')
        # A renderer can request subresources: this counts invocations, not all browser HTTP requests.
        # Only explicitly configured public sources should use this optional browser adapter.
        resolved = canonical_url(getattr(result, 'redirected_url', None) or doc['url'])
        public_url(resolved)
        raw = (result.html or '').encode('utf-8')
        if len(raw) > self.budget['max_bytes']:
            raise FetchError('rendered_page_too_large')
        title, text, published_hint = parse_html(raw)
        doc.update(resolved_url=resolved, title=title or doc['title'], text=text,
                   published_hint=published_hint, parser='crawl4ai_rendered_html',
                   raw_sha256=digest(raw), retrieved_at=now())
        path = self.out / 'sources' / (doc['id'] + '.html')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        doc['raw_path'] = str(path.relative_to(self.out))
        self._finish(doc, target)
        return doc
