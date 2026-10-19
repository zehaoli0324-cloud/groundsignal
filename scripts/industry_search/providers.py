"""Independent search adapters. Results and summaries are leads, never evidence."""
import os
import time
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import requests

from .contracts import canonical_url, digest, now, read_json, write_json

KEYS = {'brave': 'BRAVE_SEARCH_API_KEY', 'tavily': 'TAVILY_API_KEY',
        'firecrawl': 'FIRECRAWL_API_KEY', 'deepseek': 'DEEPSEEK_API_KEY'}


def retry_seconds(value):
    try:
        return max(1, min(86400, int(value)))
    except (TypeError, ValueError):
        try:
            return max(1, min(86400, int((parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())))
        except (TypeError, ValueError, OverflowError):
            return 60


class SearchClient:
    def __init__(self, cache, budget, session=None):
        self.cache = cache
        self.budget = budget
        self.session = session or requests.Session()
        self.calls = 0

    def query(self, provider, task, limit):
        record = {'provider': provider, 'query_id': task['id'], 'query': task['query'],
                  'searched_at': now(), 'status': None, 'cached': False, 'hits': [],
                  'usage': {}, 'error_code': None}
        # Preflight happens before cache access: fixture or stale cache is never a fake live service.
        if provider in KEYS and not os.environ.get(KEYS[provider]):
            return dict(record, status='NOT_CONFIGURED', error_code='missing_' + KEYS[provider])
        if provider not in {*KEYS, 'sogou', 'so360'}:
            return dict(record, status='FAILED', error_code='unknown_provider')
        if provider == 'deepseek' and len(task['query']) > 128:
            return dict(record, status='FAILED', error_code='query_exceeds_provider_128_chars')
        cache_file = self.cache / ('query-' + digest([provider, task['query'], limit, 1]) + '.json')
        if cache_file.exists():
            cached = read_json(cache_file)
            if cached['expires_at'] > time.time():
                return dict(cached['record'], query_id=task['id'], cached=True)
        state_file = self.cache / ('provider-' + provider + '.json')
        state = read_json(state_file) if state_file.exists() else {}
        if state.get('retry_at', 0) > time.time():
            return dict(record, status='COOLDOWN', error_code='provider_retry_after')
        if self.calls >= self.budget['max_search_calls']:
            return dict(record, status='BUDGET_EXHAUSTED', error_code='max_search_calls')
        # Sequential requests and persisted spacing avoid repeatedly hitting a blocked provider.
        delay = self.budget['request_interval_seconds'] - (time.time() - state.get('last_request', 0))
        if delay > 0:
            time.sleep(delay)
        self.calls += 1
        state['last_request'] = time.time()
        write_json(state_file, state)
        started = time.monotonic()
        try:
            response, rows = self._request(provider, task['query'], limit)
            if rows is None:
                if response.status_code in {401, 402, 403, 429}:
                    state['retry_at'] = time.time() + retry_seconds(response.headers.get('Retry-After'))
                    write_json(state_file, state)
                    return dict(record, status='UNAVAILABLE', error_code='http_' + str(response.status_code))
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError('invalid_provider_payload')
                rows = self._rows(provider, payload)
                record['usage'] = {k: payload[k] for k in ('usage', 'creditsUsed') if k in payload}
            for rank, row in enumerate(rows[:limit], 1):
                try:
                    url = canonical_url(row.get('url', ''))
                except ValueError:
                    continue
                record['hits'].append({'url': url, 'title': str(row.get('title', ''))[:1000],
                                       'snippet': str(row.get('description') or row.get('snippet')
                                                      or row.get('content') or row.get('summary') or '')[:3000],
                                       'rank': rank, 'published_hint': row.get('published_date') or row.get('date')})
            record['status'] = 'OK' if record['hits'] else 'NO_RESULTS'
            record['elapsed_ms'] = round((time.monotonic() - started) * 1000)
            write_json(cache_file, {'expires_at': time.time() + self.budget['cache_ttl_seconds'], 'record': record})
        except requests.RequestException as exc:
            record.update(status='FAILED', error_code=type(exc).__name__)
        except (ValueError, KeyError, TypeError) as exc:
            record.update(status='FAILED', error_code='invalid_provider_payload')
        except RuntimeError as exc:
            # Legacy parsing exposes a stable code, never its raw page or credentials.
            code = getattr(exc, 'code', 'legacy_search_error')
            record.update(status='FAILED', error_code=code)
            if code == 'blocked':
                state['retry_at'] = time.time() + 1800
                write_json(state_file, state)
        return record

    def _request(self, provider, query, limit):
        timeout = (5, self.budget['timeout_seconds'])
        key = os.environ.get(KEYS.get(provider, ''), '')
        headers = {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}
        if provider == 'brave':
            return self.session.get('https://api.search.brave.com/res/v1/web/search',
                params={'q': query, 'count': limit}, headers={'X-Subscription-Token': key}, timeout=timeout), None
        if provider == 'tavily':
            return self.session.post('https://api.tavily.com/search', headers=headers,
                json={'query': query, 'max_results': limit, 'search_depth': 'basic',
                      'include_answer': False, 'include_raw_content': False, 'include_usage': True}, timeout=timeout), None
        if provider == 'firecrawl':
            return self.session.post('https://api.firecrawl.dev/v2/search', headers=headers,
                json={'query': query, 'limit': limit, 'sources': ['web']}, timeout=timeout), None
        if provider == 'deepseek':
            return self.session.post('https://api.deepseek.com/v1/tools/search', headers=headers,
                json={'query': query, 'count': limit, 'need_content': False}, timeout=timeout), None
        from search_sources import parse_sogou, parse_360
        url, param = ('https://www.sogou.com/web', 'query') if provider == 'sogou' else ('https://www.so.com/s', 'q')
        response = self.session.get(url, params={param: query}, timeout=timeout)
        if response.status_code != 200:
            return response, None
        response.encoding = response.apparent_encoding
        rows = (parse_sogou if provider == 'sogou' else parse_360)(response.text, '', limit)
        return response, rows

    @staticmethod
    def _rows(provider, payload):
        if provider == 'brave':
            web = payload.get('web')
            rows = web.get('results') if isinstance(web, dict) else None
        elif provider == 'firecrawl':
            if not payload.get('success'):
                raise ValueError('provider_unsuccessful')
            data = payload.get('data', {})
            rows = data if isinstance(data, list) else data.get('web')
        else:
            rows = payload.get('results')
        if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
            raise ValueError('invalid_results')
        return rows
