import json
from pathlib import Path
import tempfile
import time
import threading
from unittest.mock import patch
from src.desktop import legacy_storage as storage
import unittest

from src.core.services.jobs import JobService
from src.desktop.runtime import DesktopRuntime
from test_job_service import FakeExecutor, wait_for


class DesktopRuntimeTests(unittest.TestCase):
    def make(self, root):
        service = JobService(root / 'runtime', executor_factory=FakeExecutor,
                             min_free_bytes=0, shutdown_grace=.1, cancel_grace=.1)
        calls = []
        history = root / 'settings.json'
        if not history.exists():
            history.write_text(json.dumps({'unknown': {'preserved': True}, 'history': []}))
        runtime = DesktopRuntime(root / 'runtime', service=service,
                                 chatbot_action=lambda text, url: calls.append((text, url)),
                                 folder_action=lambda path: calls.append(path), history_path=history)
        return runtime, calls

    def options(self, root):
        return {'user_inputs': {'student_id': '123', 'password': 'private-password', 'api_key': 'private-key'},
                'engine': 'clipboard', 'model_name': 'claude-web', 'summary_prompt': 'fixed prompt',
                'stt_engine': 'faster-whisper', 'stt_model': 'tiny',
                'stt_params': {'api_key': 'stt-secret', 'client_id': 'id', 'client_secret': 'secret'},
                'downloads_dir': str(root / 'results'), 'save_video_dir': None, 'auto_open_folder': True}

    def exported(self, runtime, job_id):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            detail = runtime.service.detail(runtime.context, job_id)
            if detail['current_attempt_id'] in runtime.state.read().get('exports', {}):
                # Host actions are dispatched after the export is persisted.
                time.sleep(.05)
                return detail
            time.sleep(.02)
        self.fail('No desktop export')

    def test_export_history_fixed_settings_and_restart_idempotence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'lecture.txt'
            source.write_text('original')
            runtime, calls = self.make(root)
            runtime.start()
            try:
                options = self.options(root)
                job_id = runtime.submit([], [str(source)], options)[0]
                options['summary_prompt'] = 'changed'
                job = self.exported(runtime, job_id)
                folder = runtime.export(job)
                self.assertTrue((folder / 'lecture_프롬프트.txt').exists())
                self.assertIn('fixed prompt', (folder / 'lecture_프롬프트.txt').read_text())
                self.assertEqual(source.read_text(), 'original')
                saved = json.loads((root / 'settings.json').read_text())
                self.assertEqual(saved['unknown'], {'preserved': True})
                self.assertEqual(len(saved['history']), 1)
                self.assertEqual(saved['history'][0]['result_kind'], 'manual_ready')
                self.assertEqual(len(calls), 2)
                self.assertEqual(calls[0][1], 'https://claude.ai/')
                state = (root / 'runtime/desktop.json').read_text()
                self.assertNotIn('private-password', state)
                self.assertNotIn('private-key', state)
                self.assertNotIn('stt-secret', state)
            finally:
                runtime.close()
            restarted, reopened = self.make(root)
            restarted.start()
            try:
                self.assertEqual(len(restarted.jobs()), 1)
                self.assertEqual(restarted.export(restarted.jobs()[0]), folder)
                time.sleep(.1)
                self.assertEqual(reopened, [])
                self.assertEqual(len(json.loads((root / 'settings.json').read_text())['history']), 1)
            finally:
                restarted.close()

    def test_cancel_retry_and_subscriber_detachment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'lecture.txt'
            source.write_text('original')
            runtime, calls = self.make(root)
            # Queued cancellation is deterministic before workers start.
            job_id = runtime.submit([], [str(source)], self.options(root))[0]
            job = runtime.jobs()[0]
            runtime.cancel(job_id, job['current_attempt_id'])
            cancelled = runtime.jobs()[0]
            self.assertEqual(cancelled['status'], 'cancelled')
            runtime.retry(job_id, cancelled['current_attempt_id'])
            updates = []
            unsubscribe = runtime.subscribe(lambda job, message: updates.append(job))
            unsubscribe()
            runtime.start()
            try:
                detail = self.exported(runtime, job_id)
                self.assertEqual(len(detail['attempts']), 2)
                self.assertEqual(updates, [])
                self.assertTrue(source.exists())
            finally:
                runtime.close()

    def test_unsupported_file_does_not_create_jobs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime, _ = self.make(root)
            try:
                with self.assertRaises(ValueError):
                    runtime.submit([], [str(root / 'unsupported.exe')], self.options(root))
                self.assertEqual(runtime.jobs(), [])
            finally:
                runtime.close()

    def test_export_failure_can_be_retried_without_duplicate_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'lecture.txt'
            source.write_text('original')
            runtime, _ = self.make(root)
            options = self.options(root)
            blocked = root / 'blocked'
            blocked.write_text('not a directory')
            options['downloads_dir'] = str(blocked)
            job_id = runtime.submit([], [str(source)], options)[0]
            # Keep the observer stopped to control export error/retry deterministically.
            runtime.service.start()
            try:
                job = wait_for(runtime.service, job_id, {'completed'})
                with self.assertRaises(OSError):
                    runtime.export(job)
                self.assertEqual(runtime.state.read().get('exports', {}), {})
                blocked.unlink()
                folder = runtime.export(job)
                self.assertTrue((folder / 'lecture_프롬프트.txt').exists())
                runtime.export(job)
                self.assertEqual(len(runtime.history.read()['history']), 1)
            finally:
                runtime.close()

    def test_history_update_and_legacy_setting_mutation_share_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime, _ = self.make(root)
            loaded, release, written = threading.Event(), threading.Event(), threading.Event()
            real_load = storage.load_settings
            def paused_load():
                value = real_load()
                loaded.set()
                if not release.wait(3):
                    raise RuntimeError('test release timeout')
                return value
            def history_update():
                runtime.history.update(lambda raw: raw['history'].append({'lecture_name': 'new'}))
                written.set()
            try:
                with patch.object(storage, 'get_settings_path', return_value=str(root / 'settings.json')):
                    with patch.object(storage, 'load_settings', side_effect=paused_load):
                        setter = threading.Thread(target=storage.set_debug_mode, args=(True,))
                        setter.start()
                        self.assertTrue(loaded.wait(2))
                        writer = threading.Thread(target=history_update)
                        writer.start()
                        try:
                            self.assertFalse(written.wait(.05))
                        finally:
                            release.set()
                            setter.join(3)
                            writer.join(3)
                    self.assertTrue(storage.get_debug_mode())
                    self.assertEqual(len(storage.load_history()), 1)
            finally:
                runtime.close()

    def test_url_history_retains_original_url_and_downloaded_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime, _ = self.make(root)
            runtime.start()
            url = 'https://canvas.ssu.ac.kr/courses/123/modules/items/456'
            try:
                job_id = runtime.submit([url], [], self.options(root))[0]
                self.exported(runtime, job_id)
                entry = runtime.history.read()['history'][0]
                self.assertEqual(entry['url'], url)
                self.assertEqual(entry['lecture_name'], 'stage-1.txt')
            finally:
                runtime.close()
