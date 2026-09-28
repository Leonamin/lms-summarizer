import ast
import concurrent.futures
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from src.core.models.settings import PromptSettings
from src.core.repositories.json_store import JsonStore
from src.core.repositories.settings import CacheRepository, HistoryRepository
from src.core.repositories.paths import DataPaths
from src.core.repositories.secrets import SecretRepository
from src.core.services.settings import snapshot_settings
from src.desktop.legacy_import import read_legacy

ROOT = Path(__file__).resolve().parents[1]

class CoreTests(unittest.TestCase):
    def test_framework_free_imports(self):
        script = '''
import sys, importlib.abc, importlib
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in ('flet','pyperclip','fastapi') or fullname.startswith('src.gui'):
            raise AssertionError(fullname)
sys.meta_path.insert(0, Block())
from pathlib import Path
for p in Path('src/core').rglob('*.py'):
    importlib.import_module('.'.join(p.with_suffix('').parts))
'''
        subprocess.run([sys.executable, "-c", script], cwd=ROOT, check=True)

    def test_pipeline_dependencies(self):
        for directory in ('core', 'audio_pipeline', 'video_pipeline', 'summarize_pipeline'):
            for path in (ROOT / 'src' / directory).rglob('*.py'):
                for node in ast.walk(ast.parse(path.read_text())):
                    names = [node.module or ''] if isinstance(node, ast.ImportFrom) else [a.name for a in node.names] if isinstance(node, ast.Import) else []
                    for name in names:
                        self.assertFalse(name.startswith(('src.gui', 'src.user_setting', 'flet', 'fastapi', 'pyperclip')), str(path))

    def test_atomic_updates_and_history(self):
        with tempfile.TemporaryDirectory() as root:
            def append(i):
                HistoryRepository(Path(root)).append({'id': i})
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(append, range(80)))
            self.assertEqual(len(HistoryRepository(Path(root)).read()), 80)
            store = JsonStore(Path(root) / 'data.json')
            store.write({'old': True})
            with patch('os.replace', side_effect=OSError('simulated')):
                with self.assertRaises(OSError):
                    store.write({'new': True})
            self.assertEqual(store.read(), {'old': True})

    def test_secrets_owner_and_version(self):
        with tempfile.TemporaryDirectory() as root:
            repo = SecretRepository(Path(root)/'secrets')
            a = repo.put('local', 'openai', 'first')
            b = repo.put('local', 'openai', 'second')
            self.assertEqual(repo.get('local', a), 'first')
            self.assertEqual(repo.get('local', b), 'second')
            with self.assertRaises(KeyError):
                repo.get('other', a)
            self.assertEqual(os.stat(repo.root).st_mode & 0o777, 0o700)
            self.assertEqual(os.stat(repo._store(a).path).st_mode & 0o777, 0o600)
            with self.assertRaises(ValueError):
                repo.get('local', '../settings')

    def test_cache_and_paths_isolation(self):
        with tempfile.TemporaryDirectory() as root:
            cache = CacheRepository(Path(root))
            cache.put('local', 'account-a', 'courses', [1])
            self.assertEqual(cache.get('local', 'account-a', 'courses'), [1])
            self.assertEqual(cache.get('local', 'account-b', 'courses'), [])
            self.assertEqual(cache.get('other', 'account-a', 'courses'), [])
            self.assertEqual(cache.get('local', 'account-a', 'courses', -1), [])
            with self.assertRaises(ValueError):
                DataPaths(Path(root), Path(root)).file('../outside')

    def test_legacy_preserved_and_normalized(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/'settings.json'
            raw = {'user_inputs': {'api_key': 'old-key', 'password': 'secret'},
                   'stt_api_keys': {'openai-compatible': 'stt-key', 'openai-compatible-base-url': 'http://localhost', 'openai-compatible-model': 'model'},
                   'summary_prompt': 'custom', 'history': [{'summary_path': 'unchanged'}],
                   'course_cache': {'courses': [{'id':'1'}]}}
            path.write_text(json.dumps(raw))
            before = path.read_bytes()
            data = read_legacy(path)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(data.secrets['summary:gemini'], 'old-key')
            self.assertEqual(data.settings['stt_base_url'], 'http://localhost')
            self.assertEqual(data.settings['resolved_prompt'], 'custom')
            self.assertEqual(data.history, raw['history'])
            self.assertEqual(data.courses, raw['course_cache']['courses'])
            self.assertNotIn('secret', json.dumps(data.settings))

    def test_snapshot_copies_and_rejects_secrets(self):
        settings = {'stt_params': {'repeat_threshold': 4}}
        revision = snapshot_settings('local', settings, PromptSettings(), {'openai':'version'})
        settings['stt_params']['repeat_threshold'] = 10
        self.assertEqual(json.loads(revision.settings_json)['stt_params']['repeat_threshold'], 4)
        with self.assertRaises(ValueError):
            snapshot_settings('local', {'stt_params': {'api_key':'secret'}}, PromptSettings(), {})

    def test_legacy_desktop_storage(self):
        from src.desktop import legacy_storage as legacy
        with tempfile.TemporaryDirectory() as root:
            with patch.object(legacy, 'get_settings_path', return_value=str(Path(root)/'settings.json')):
                legacy.save_settings({'unknown': {'preserve': True}, 'history': [], 'course_cache': {'courses': [1], 'cached_at': '2099-01-01T00:00:00'}})
                with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                    list(pool.map(lambda i: legacy.add_history_entry({'id': i}), range(40)))
                legacy.set_stt_model('new')
                self.assertEqual(len(legacy.load_history()), 40)
                self.assertEqual(legacy.load_course_cache(), [1])
                self.assertTrue(legacy.load_settings()['unknown']['preserve'])

if __name__ == '__main__':
    unittest.main()
