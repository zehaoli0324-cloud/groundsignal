import threading
import unittest
import test_collector_ui as base

class BatchTests(unittest.TestCase):
    tearDown = base.UITests.tearDown
    wait_job = base.UITests.wait_job
    def setUp(self):
        base.UITests.setUp(self)
        directory = self.root / '01-公司'
        directory.mkdir()
        for name in ['甲公司', '乙公司', '丙公司']:
            (directory / (name + '.md')).write_text('手工笔记', encoding='utf-8')
        self.calls = []
        def collector(name, vault, limit, progress, force_refresh):
            self.calls.append((name, force_refresh))
            if name == '乙公司':
                raise RuntimeError('访问受限')
            return {'report': str(vault / (name + '-report.md')), 'changed': False}
        self.app.collector = collector

    def test_all_continues_after_failure_and_retry_only_failed(self):
        self.app.start_update(all_companies=True)
        self.wait_job()
        self.assertEqual(len(self.calls), 3)
        self.assertTrue(all(refresh for _, refresh in self.calls))
        self.assertEqual(self.app.job['succeeded'], 2)
        self.assertEqual(self.app.job['failed'], 1)
        self.app.start_update(retry_failed=True)
        self.wait_job()
        self.assertEqual(self.calls[-1][0], '乙公司')
        self.assertEqual(len(self.calls), 4)

    def test_selection_validation_and_deduplication(self):
        for names in [[], ['不存在'], '../bad']:
            with self.assertRaises(ValueError):
                self.app.start_update(names)
        self.app.start_update(['甲公司', '甲公司'])
        self.wait_job()
        self.assertEqual(self.calls, [('甲公司', True)])
        snapshot = self.app.state()
        snapshot['job']['items'][0]['name'] = 'changed'
        self.assertEqual(self.app.job['items'][0]['name'], '甲公司')

    def test_cancel_finishes_current_and_skips_remaining(self):
        entered, release = threading.Event(), threading.Event()
        def collector(name, vault, limit, **kwargs):
            entered.set()
            release.wait(3)
            return {'report': str(vault / 'report.md')}
        self.app.collector = collector
        self.app.start_update(['甲公司', '乙公司', '丙公司'])
        self.assertTrue(entered.wait(2))
        try:
            with self.assertRaises(ValueError):
                self.app.start_update(['甲公司'])
            self.app.cancel_update()
        finally:
            release.set()
        self.wait_job()
        self.assertEqual(self.app.job['status'], 'cancelled')
        self.assertEqual([x['status'] for x in self.app.job['items']], ['done', 'skipped', 'skipped'])
