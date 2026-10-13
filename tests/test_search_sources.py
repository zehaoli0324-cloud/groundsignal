import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import search_sources as sources

SOGOU = '''<title>测试公司 - 搜狗搜索</title><div class="results"><div class="rb">
<h3 class="pt"><a href="/link?url=redirect">测试公司官网</a></h3>
<div class="ft">测试公司介绍</div><a class="citeLinkClass" href="https://example.com/about">官网</a>
</div><div class="rb"><h3 class="pt"><a href="https://unrelated.example">其他公司</a></h3></div></div>'''
SO360 = '''<title>测试公司 - 搜索</title><li><h3 class="res-title"><a data-mdurl="https://example.com/about">测试公司官网</a></h3></li>'''
CHALLENGE = '<title>访问异常页面</title><p>请输入验证码以便正常访问</p>'


def response(text):
    return Mock(text=text, url='https://search.example/results')


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cache = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_200_challenge_is_not_no_match(self):
        with self.assertRaises(sources.SearchFailure) as caught:
            sources.parse_360(CHALLENGE, '测试公司', 6)
        self.assertEqual(caught.exception.code, 'blocked')

    def test_sogou_direct_source_and_relevance(self):
        items = sources.parse_sogou(SOGOU, '测试公司', 6)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['url'], 'https://example.com/about')

    def test_layout_change_separate_from_no_match(self):
        with self.assertRaises(sources.SearchFailure) as caught:
            sources.parse_sogou('<title>搜索</title><div>new layout</div>', '测试', 6)
        self.assertEqual(caught.exception.code, 'parse_error')
        with self.assertRaises(sources.SearchFailure) as caught:
            sources.parse_sogou(SOGOU, '完全不同公司', 6)
        self.assertEqual(caught.exception.code, 'no_match')

    def test_map_widget_is_not_a_company_source(self):
        markup = SOGOU + '''<div class="vrwrap"><h3 class="vr-title"><a href="https://apis.map.qq.com/search">搜索测试公司</a></h3>
        <div data-url="https://sogo.com/data_is_json/"></div></div>'''
        self.assertEqual(len(sources.parse_sogou(markup, '测试公司', 6)), 1)

    def test_fallback_after_block_and_durable_cooldown(self):
        with patch.object(sources, 'get_response', side_effect=[response(CHALLENGE), response(SO360)]) as get:
            result = sources.search(Mock(), '测试公司', 6, cache_dir=self.cache, providers=['sogou', 'so360'])
        self.assertEqual(get.call_count, 2)
        self.assertEqual(result['provider'], '360')
        self.assertEqual(result['diagnostics'][0]['code'], 'blocked')
        with patch.object(sources, 'get_response') as get:
            with self.assertRaises(sources.SearchFailure) as caught:
                sources.search(Mock(), '另一家公司', 6, cache_dir=self.cache, providers=['sogou'])
        get.assert_not_called()
        self.assertEqual(caught.exception.diagnostics[0]['code'], 'cooldown')

    def test_cache_hit_uses_no_search_request(self):
        with patch.object(sources, 'get_response', return_value=response(SOGOU)) as get:
            first = sources.search(Mock(), '测试公司', 6, cache_dir=self.cache, providers=['sogou'])
            second = sources.search(Mock(), '测试公司', 6, cache_dir=self.cache, providers=['sogou'])
        self.assertEqual(get.call_count, 1)
        self.assertFalse(first['cached'])
        self.assertTrue(second['cached'])
        self.assertEqual(first['searched_at'], second['searched_at'])

    def test_refresh_bypasses_cache_and_keeps_rate_limit(self):
        with patch.object(sources, 'get_response', return_value=response(SOGOU)) as get, patch.object(sources.time, 'sleep') as sleep:
            sources.search(Mock(), '测试公司', 6, cache_dir=self.cache, providers=['sogou'])
            result = sources.search(Mock(), '测试公司', 6, cache_dir=self.cache, providers=['sogou'], force_refresh=True)
        self.assertEqual(get.call_count, 2)
        self.assertFalse(result['cached'])
        sleep.assert_called_once()

    def test_network_failure_falls_back(self):
        with patch.object(sources, 'get_response', side_effect=[requests.Timeout('secret proxy data'), response(SO360)]):
            result = sources.search(Mock(), '测试公司', 6, cache_dir=self.cache, providers=['sogou', 'so360'])
        self.assertEqual(result['diagnostics'][0]['message'], 'Timeout')
        self.assertEqual(result['provider'], '360')

    def test_429_respects_retry_after(self):
        session = Mock()
        session.get.return_value = Mock(status_code=429, headers={'Retry-After': '7200'})
        with self.assertRaises(sources.SearchFailure) as caught:
            sources.get_response(session, 'sogou', '测试')
        self.assertEqual(caught.exception.retry_after, 7200)

    def test_rate_spacing(self):
        (self.cache/'providers.json').write_text(json.dumps({'sogou': {'last_request': time.time()}}), encoding='utf-8')
        with patch.object(sources.time, 'sleep') as sleep, patch.object(sources, 'get_response', return_value=response(SOGOU)):
            sources.search(Mock(), '测试公司', 6, cache_dir=self.cache, providers=['sogou'])
        self.assertTrue(0 < sleep.call_args.args[0] <= sources.INTERVAL)

    def test_api_key_not_in_url_or_result(self):
        session = Mock()
        session.get.return_value = Mock(status_code=200, encoding='utf-8')
        with patch.dict('os.environ', {'BRAVE_SEARCH_API_KEY': 'test-secret'}):
            sources.get_response(session, 'brave_api', '测试')
        args, kwargs = session.get.call_args
        self.assertNotIn('test-secret', str(args) + str(kwargs['params']))
        self.assertEqual(kwargs['headers']['X-Subscription-Token'], 'test-secret')


if __name__ == '__main__':
    unittest.main()
