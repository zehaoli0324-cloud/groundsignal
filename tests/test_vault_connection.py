import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collector_ui import App
from vault_connection import check_vault, discover


class VaultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.vault = self.root / '中文笔记库'
        self.vault.mkdir()
        (self.vault / '.obsidian').mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_first_launch_is_disconnected_not_current_directory(self):
        app = App(self.root / 'fresh-settings.json')
        self.assertEqual(app.state()['history'], [])
        self.assertFalse(app.settings()['connected'])
        self.assertEqual(app.settings()['vault'], '')
        with self.assertRaises(ValueError):
            app.start('测试公司')

    def test_selecting_parent_gives_child_hint(self):
        with self.assertRaisesRegex(ValueError, '中文笔记库'):
            check_vault(str(self.root))

    def test_writable_check_leaves_notes_untouched(self):
        note = self.vault / '笔记.md'
        note.write_text('保留我的内容', encoding='utf-8')
        result = check_vault(str(self.vault), write_test=True)
        self.assertTrue(result['writable'])
        self.assertEqual(note.read_text(encoding='utf-8'), '保留我的内容')
        self.assertEqual(list(self.vault.glob('.groundsignal-check-*')), [])

    def test_failed_write_does_not_save_connection(self):
        path = self.root/'settings.json'
        app = App(path)
        with patch('vault_connection.tempfile.mkstemp', side_effect=PermissionError('read only')):
            with self.assertRaises(PermissionError):
                app.update_settings({'vault': str(self.vault)})
        self.assertFalse(path.exists())

    def test_successful_connection_survives_restart(self):
        path = self.root/'settings.json'
        App(path).update_settings({'vault': str(self.vault), 'max_results': 3})
        settings = App(path).settings()
        self.assertTrue(settings['connected'])
        self.assertEqual(settings['name'], '中文笔记库')
        self.assertEqual(settings['max_results'], 3)

    def test_discovery_filters_stale_and_duplicates(self):
        path = self.root/'obsidian.json'
        path.write_text(json.dumps({'vaults': {'one': {'path': str(self.vault)},
                                             'two': {'path': str(self.vault)},
                                             'old': {'path': str(self.root/'gone')}}}), encoding='utf-8')
        found = discover(path)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]['path'], str(self.vault.resolve()))


if __name__ == '__main__':
    unittest.main()
