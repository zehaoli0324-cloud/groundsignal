import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collector_ui import App, make_handler
from collect import save


class UITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / '.obsidian').mkdir()
        self.config = self.root / 'config.json'
        self.config.write_text(json.dumps({'vault': str(self.root), 'max_results': 6}), encoding='utf-8')
        self.app = App(self.config)

    def tearDown(self):
        self.temp.cleanup()

    def wait_job(self):
        deadline = time.monotonic() + 3
        while self.app.job['status'] == 'running' and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertNotEqual(self.app.job['status'], 'running')

    def test_collection_to_report_and_history(self):
        def collector(name, vault, limit, progress):
            progress('fetching', '读取资料', 0, 1)
            items = [{'title': '测试来源', 'url': 'https://example.com', 'status': 'page_fetched',
                      'snippet': '线索', 'excerpt': '测试正文'}]
            note, report = save(vault, name, 'https://example.com', items)
            return {'query': name, 'note': str(note), 'report': str(report), 'search_results': 1, 'pages_fetched': 1}
        self.app.collector = collector
        self.app.start('测试公司')
        self.wait_job()
        self.assertEqual(self.app.job['status'], 'done')
        history = self.app.history()
        self.assertEqual(len(history), 1)
        report = self.app.detail(history[0]['id'])
        self.assertEqual(report['pages'], 1)
        self.assertTrue(report['note_uri'].startswith('obsidian://open?path='))
        self.app.start('测试公司')
        self.wait_job()
        self.assertEqual(len(self.app.history()), 1)

    def test_failed_search_has_no_files(self):
        def failure(*args, **kwargs):
            raise RuntimeError('无结果')
        self.app.collector = failure
        self.app.start('测试公司')
        self.wait_job()
        self.assertEqual(self.app.job['status'], 'error')
        self.assertEqual(self.app.history(), [])
        self.assertFalse((self.root / '01-公司').exists())

    def test_running_job_cannot_be_duplicated_or_redirected(self):
        release = threading.Event()
        def blocking(*args, **kwargs):
            release.wait(3)
            raise RuntimeError('测试结束')
        self.app.collector = blocking
        self.app.start('测试公司')
        try:
            with self.assertRaises(ValueError):
                self.app.start('另一公司')
            with self.assertRaises(ValueError):
                self.app.update_settings({'vault': str(self.root)})
        finally:
            release.set()
            self.wait_job()

    def test_settings_validation_and_persistence(self):
        with self.assertRaises(ValueError):
            self.app.update_settings({'vault': 'relative'})
        with self.assertRaises(ValueError):
            self.app.update_settings({'vault': str(self.root), 'max_results': 100})
        self.app.update_settings({'vault': str(self.root), 'max_results': 3})
        self.assertEqual(App(self.config).settings()['max_results'], 3)

    def test_report_cannot_escape_vault(self):
        for name in ('../config', '..\\config', 'C:config', ''):
            with self.assertRaises(ValueError):
                self.app.detail(name)

    def test_http_page_state_and_request_protection(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(self.app))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        session = requests.Session()
        session.trust_env = False
        url = f'http://127.0.0.1:{server.server_port}'
        try:
            page = session.get(url, timeout=3)
            self.assertEqual(page.status_code, 200)
            self.assertIn('搜索并保存', page.text)
            self.assertNotIn('__TOKEN__', page.text)
            self.assertEqual(session.get(url+'/api/state', timeout=3).status_code, 200)
            self.assertEqual(session.post(url+'/api/collect', json={'name': '测试'}, timeout=3).status_code, 403)
            headers = {'X-GroundSignal-Token': self.app.token, 'Origin': 'https://other.example'}
            self.assertEqual(session.post(url+'/api/collect', json={'name': '测试'}, headers=headers, timeout=3).status_code, 403)
            headers.pop('Origin')
            self.assertEqual(session.post(url+'/api/collect', json={'name': '../逃逸'}, headers=headers, timeout=3).status_code, 400)
            self.assertEqual(session.get(url+'/api/state', headers={'Host': 'other.example'}, timeout=3).status_code, 403)
        finally:
            session.close()
            server.shutdown()
            server.server_close()
            worker.join()


if __name__ == '__main__':
    unittest.main()
