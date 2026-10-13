import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import collect
from search_sources import parse_360, SearchFailure


class CollectorTests(unittest.TestCase):
    def test_search_filters_unrelated_and_duplicates(self):
        markup = '''<li><h3 class="res-title"><a data-mdurl="https://example.com/a">测试公司介绍</a></h3></li>
        <h3 class="res-title"><a data-mdurl="https://example.com/a">测试公司</a></h3>
        <h3 class="res-title"><a data-mdurl="https://example.com/b">其他公司</a></h3>'''
        results = parse_360(markup, '测试公司', 6)
        self.assertEqual(len(results), 1)

    def test_empty_search_does_not_write(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(collect, 'search', side_effect=SearchFailure('blocked', '验证码')):
                with self.assertRaises(RuntimeError):
                    collect.collect('测试公司', temp)
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_title_only_is_not_body(self):
        response = Mock(text='<html><head><title>测试公司股份有限公司的详细介绍及最新持股列表</title></head><body>登录</body></html>',
                        headers={'Content-Type': 'text/html'})
        with patch.object(collect, 'fetch', return_value=response):
            result = collect.enrich(Mock(), {'title': 'test', 'url': 'https://example.com', 'snippet': ''}, '测试公司')
        self.assertEqual(result['status'], 'search_only')

    def test_repeat_preserves_user_content_and_one_block(self):
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp)
            note = vault / '01-公司/测试公司.md'
            note.parent.mkdir()
            original = '---\nevidence: SUPPORTED\n---\n# 我的研究\n[[其他公司]]\n'
            note.write_text(original, encoding='utf-8')
            items = [{'title': '来源', 'url': 'https://example.com', 'snippet': '线索',
                      'status': 'search_only', 'excerpt': ''}]
            for _ in range(2):
                collect.save(vault, '测试公司', 'https://www.so.com/s', items)
            text = note.read_text(encoding='utf-8')
            self.assertTrue(text.startswith(original))
            self.assertEqual(text.count(collect.START), 1)
            self.assertEqual(len(list((vault/'09-采集记录').glob('*.md'))), 1)

    def test_bad_name(self):
        for name in ['../逃逸', 'a/b', 'NUL', 'a[[b]]', 'a\n']:
            with self.assertRaises(ValueError):
                collect.validate_name(name)

    def test_broken_marker_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            note = Path(temp) / '01-公司/测试公司.md'
            note.parent.mkdir()
            note.write_text(collect.START, encoding='utf-8')
            with self.assertRaises(ValueError):
                collect.save(Path(temp), '测试公司', '', [])
            self.assertEqual(note.read_text(encoding='utf-8'), collect.START)

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(collect, 'search', return_value={'search_url': 'https://example.com', 'items': []}):
                collect.collect('测试公司', temp, dry_run=True)
            self.assertEqual(list(Path(temp).iterdir()), [])


if __name__ == '__main__':
    unittest.main()
