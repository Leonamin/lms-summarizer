import errno
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import psutil

from src.core.models.jobs import Source, StageResult
from src.core.models.settings import PromptSettings
from src.core.services.jobs import JobService
from src.core.services.settings import snapshot_settings
from src.desktop.legacy_import import read_legacy
from test_job_service import FakeExecutor, OWNER, revision, wait_for


class ShutdownChildExecutor:
    def execute(self, command, cancelled):
        deadline = time.monotonic() + 10
        while not cancelled.is_set() and time.monotonic() < deadline:
            time.sleep(0.01)
        child = subprocess.Popen(
            [sys.executable, '-c', 'import time; time.sleep(30)'],
            start_new_session=True,
        )
        Path(json.loads(command.settings_json)['pid_marker']).write_text(str(child.pid))
        output = Path(command.output_dir) / 'output.txt'
        output.write_text('fixture')
        return StageResult(command.token, str(output), 'prompt')

    def close(self):
        pass


class ReviewRegressionTests(unittest.TestCase):
    def source(self, service, root):
        path = Path(root) / 'source.txt'
        path.write_text('fixture')
        return Source.file(service.import_file(OWNER, path))

    def test_staging_errors_fail_only_the_affected_job(self):
        for error, expected in ((errno.ENOSPC, 'disk_full'), (errno.EACCES, 'stage_failed')):
            with self.subTest(error=error), tempfile.TemporaryDirectory() as root:
                with JobService(Path(root) / 'data', executor_factory=FakeExecutor,
                                min_free_bytes=0, shutdown_grace=0.1) as service:
                    source = self.source(service, root)
                    real_mkdir = Path.mkdir
                    failed_once = []

                    def fail_staging(path, *args, **kwargs):
                        if path.name == '.part' and not failed_once:
                            failed_once.append(path)
                            # Simulate failure after partially creating parents.
                            real_mkdir(path.parent, parents=True, exist_ok=True)
                            raise OSError(error, 'fixture')
                        return real_mkdir(path, *args, **kwargs)

                    with patch.object(Path, 'mkdir', fail_staging):
                        jobs = service.submit(OWNER, [source, source], revision(), idempotency_key='disk')
                        failed = wait_for(service, jobs[0], {'failed'})
                        wait_for(service, jobs[1], {'completed'})
                    self.assertEqual(failed['attempts'][-1]['error_code'], expected)
                    self.assertFalse(failed_once[0].parent.exists())
                    self.assertTrue(service.health()['running'])
                    self.assertIsNone(service.health()['error_code'])

    @unittest.skipIf(os.name == 'nt', 'Detached Unix sessions use worker-side cleanup')
    def test_shutdown_cleans_children_created_after_polling_stops(self):
        with tempfile.TemporaryDirectory() as root:
            service = JobService(Path(root) / 'data', executor_factory=ShutdownChildExecutor,
                                 min_free_bytes=0, shutdown_grace=2)
            marker = Path(root) / 'child.pid'
            try:
                service.start()
                job = service.submit(OWNER, [self.source(service, root)],
                                     revision({'pid_marker': str(marker)}), idempotency_key='child')[0]
                wait_for(service, job, {'running'})
                service.close()
                pid = int(marker.read_text())
                self.assertTrue(not psutil.pid_exists(pid) or
                                psutil.Process(pid).status() == psutil.STATUS_ZOMBIE)
            finally:
                service.close()
                if marker.exists():
                    try:
                        psutil.Process(int(marker.read_text())).kill()
                    except psutil.NoSuchProcess:
                        pass

    def test_import_extracts_nested_credentials_without_changing_legacy_file(self):
        for engine in ('openai-whisper', 'openai-compatible', 'returnzero'):
            with self.subTest(engine=engine), tempfile.TemporaryDirectory() as root:
                path = Path(root) / 'legacy.json'
                raw = {'stt_engine': engine, 'stt_params': {
                    'api_key': 'nested-fixture', 'client_id': 'client-fixture',
                    'client_secret': 'secret-fixture', 'repeat_threshold': 4,
                    'base_url': 'http://localhost/v1', 'model_name': 'fixture-model',
                }}
                path.write_text(json.dumps(raw))
                original = path.read_bytes()
                imported = read_legacy(path)
                self.assertEqual(path.read_bytes(), original)
                self.assertEqual(imported.settings['stt_params'], {'repeat_threshold': 4})
                self.assertEqual(imported.settings['stt_base_url'], 'http://localhost/v1')
                self.assertEqual(imported.settings['stt_compatible_model'], 'fixture-model')
                self.assertEqual(imported.secrets[f'stt:{engine}'], 'nested-fixture')
                self.assertEqual(imported.secrets['returnzero_client_secret'], 'secret-fixture')
                snapshot_settings('local', imported.settings, PromptSettings(), {})

    def test_import_prefers_dedicated_stt_key_over_stale_params(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'legacy.json'
            path.write_text(json.dumps({'stt_engine': 'openai-whisper',
                'stt_api_keys': {'openai-whisper': 'current-fixture'},
                'stt_params': {'api_key': 'stale-fixture'}}))
            imported = read_legacy(path)
            self.assertEqual(imported.secrets['stt:openai-whisper'], 'current-fixture')
            self.assertNotIn('api_key', imported.settings['stt_params'])

    def test_stage_timeout_preserves_pending_cancellation(self):
        with tempfile.TemporaryDirectory() as root:
            with JobService(Path(root) / 'data', executor_factory=FakeExecutor,
                            min_free_bytes=0, shutdown_grace=0.1,
                            cancel_grace=2, stage_timeout=0.5) as service:
                job = service.submit(OWNER, [self.source(service, root)],
                                     revision({'delay': 30, 'ignore_cancel': True}),
                                     idempotency_key='cancel')[0]
                running = wait_for(service, job, {'running'})
                service.cancel(OWNER, job, running['current_attempt_id'])
                result = wait_for(service, job, {'cancelled', 'failed'})
                self.assertEqual(result['status'], 'cancelled')
                self.assertEqual(result['attempts'][-1]['error_code'], 'cancelled')

    def test_idle_heartbeat_waits_despite_supervisor_notifications(self):
        with tempfile.TemporaryDirectory() as root:
            with JobService(Path(root) / 'data', executor_factory=FakeExecutor,
                            min_free_bytes=0, shutdown_grace=0.1) as service:
                subscription = service.subscribe(OWNER, heartbeat=0.15)
                try:
                    started = time.monotonic()
                    events = [next(subscription) for _ in range(3)]
                    self.assertTrue(all(e['type'] == 'heartbeat' for e in events))
                    self.assertGreaterEqual(time.monotonic() - started, 0.4)
                    job = service.submit(OWNER, [self.source(service, root)],
                                         revision(), idempotency_key='event')[0]
                    event = next(subscription)
                    self.assertEqual(event['type'], 'job.updated')
                    self.assertEqual(event['job_id'], job)
                finally:
                    subscription.close()
