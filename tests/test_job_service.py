import json
import itertools
import multiprocessing
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from src.core.models.jobs import Source, StageResult, ServiceError
from src.core.models.settings import PromptSettings, UserContext
from src.core.models.stages import PipelineStage
from src.core.services.settings import snapshot_settings
from src.core.services.jobs import JobService

OWNER = UserContext()

def revision(settings=None, secrets=None):
    return snapshot_settings('local', {'ai_engine':'clipboard', **(settings or {})},
                             PromptSettings(mode='custom', custom_prompt='fixed prompt'), secrets or {})

class FakeExecutor:
    """Deterministic stage adapter; concurrency and cancellation use real processes."""
    def __init__(self):
        self.fingerprint = None

    def execute(self, command, cancelled):
        settings = json.loads(command.settings_json)
        if settings.get('spawn_child'):
            child = subprocess.Popen([os.sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=os.name != 'nt')
            (Path(command.output_dir)/'child.pid').write_text(str(child.pid))
        delay = settings.get('delay', 0.08)
        deadline = time.monotonic() + delay
        while time.monotonic() < deadline:
            if cancelled.is_set() and not settings.get('ignore_cancel'):
                raise ServiceError('cancelled')
            time.sleep(0.01)
        if settings.get('fail_stage') == int(command.token.stage):
            raise RuntimeError('secret-value https://sensitive.example/signed?token=secret')
        output = Path(command.output_dir)/f'stage-{int(command.token.stage)}.txt'
        output.write_text(command.resolved_prompt+' '+str(command.credentials.get('summary_api_key', '')))
        kind = {1:'video',2:'audio',3:'transcript',4:'prompt'}[command.token.stage]
        reused = command.settings_json == self.fingerprint
        self.fingerprint = command.settings_json
        return StageResult(command.token, str(output), kind, model_reused=reused)

    def close(self):
        pass

def wait_for(service, job_id, statuses, timeout=8):
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        detail = service.detail(OWNER, job_id)
        if detail['status'] in statuses:
            return detail
        if service._fatal:
            raise AssertionError('supervisor failed: '+service._fatal)
        time.sleep(0.015)
    raise AssertionError(f"Timeout: {service.detail(OWNER, job_id)}")

def crash_server(root, pipe):
    service = JobService(Path(root), executor_factory=FakeExecutor, min_free_bytes=0, shutdown_grace=0.1)
    service.start()
    path = Path(root)/'client.txt'
    path.write_text('input')
    input_id = service.import_file(OWNER, path)
    jobs = service.submit(OWNER, [Source.file(input_id), Source.file(input_id)], revision({'delay':30,'ignore_cancel':True}), idempotency_key='crash')
    wait_for(service, jobs[0], {'running'})
    pipe.send((jobs, [slot['process'].pid for slot in service._slots.values()]))
    time.sleep(60)

class JobServiceTests(unittest.TestCase):
    def make(self, root, **kwargs):
        return JobService(Path(root), executor_factory=FakeExecutor, min_free_bytes=0,
                          cancel_grace=0.1, shutdown_grace=0.1, **kwargs)

    def file(self, service, root, suffix='.txt'):
        path = Path(root)/('client'+suffix)
        path.write_text('input')
        return service.import_file(OWNER,path)

    def test_pipeline_overlap_single_slots_and_persistence(self):
        with tempfile.TemporaryDirectory() as root:
            service = self.make(root)
            with service:
                jobs = service.submit(OWNER,[Source.url(f'https://canvas.ssu.ac.kr/courses/{i}') for i in range(4)],revision({'delay':0.16}),idempotency_key='batch')
                details = [wait_for(service,j,{'completed'}) for j in jobs]
                intervals = {}
                for detail in details:
                    self.assertEqual(detail['result_kind'],'manual_ready')
                    for stage in detail['attempts'][0]['stages']:
                        intervals.setdefault(stage['stage'],[]).append((stage['started_at'],stage['ended_at']))
                for stage_intervals in intervals.values():
                    ordered = sorted(stage_intervals)
                    self.assertTrue(all(left[1] <= right[0] for left,right in zip(ordered,ordered[1:])))
                self.assertTrue(any(a[0] < b[1] and b[0] < a[1] for a in intervals[1] for b in intervals[2]))
                self.assertTrue(any(max(i[0] for i in group) < min(i[1] for i in group)
                                    for group in itertools.product(*(intervals[stage] for stage in (1,2,3,4)))))
                first = details[0]
                artifacts = {a['kind']:a for a in first['artifacts']}
                self.assertEqual(artifacts['audio']['state'],'deleted')
                self.assertEqual(artifacts['transcript']['state'],'complete')
                snapshot = service.list_jobs(OWNER)
                self.assertEqual(len(snapshot['jobs']),4)
                self.assertGreater(snapshot['event_cursor'],0)
                events = service.events_since(OWNER)['events']
                self.assertTrue(any(e['payload'].get('model_reused') for e in events))
            with self.make(root) as restarted:
                self.assertEqual(restarted.detail(OWNER,jobs[0])['status'],'completed')

    def test_queue_cancel_retry_and_dedup(self):
        with tempfile.TemporaryDirectory() as root:
            service = self.make(root)
            source = Source.file(self.file(service,root))
            settings = revision()
            jobs = service.submit(OWNER,[source],settings,idempotency_key='submit')
            self.assertEqual(service.submit(OWNER,[source],settings,idempotency_key='submit'),jobs)
            with self.assertRaises(ServiceError) as exc:
                service.submit(OWNER,[source],revision(),idempotency_key='submit')
            self.assertEqual(exc.exception.code,'idempotency_conflict')
            old = service.detail(OWNER,jobs[0])['current_attempt_id']
            service.cancel(OWNER,jobs[0],old)
            attempt = service.retry(OWNER,jobs[0],old,idempotency_key='retry')
            self.assertEqual(service.retry(OWNER,jobs[0],old,idempotency_key='retry'),attempt)
            with self.assertRaises(ServiceError):
                service.retry(OWNER,jobs[0],attempt,idempotency_key='different')
            with service:
                detail = wait_for(service,jobs[0],{'completed'})
                self.assertEqual([a['status'] for a in detail['attempts']],['cancelled','completed'])

    def test_forced_cancel_tree_and_late_result(self):
        with tempfile.TemporaryDirectory() as root:
            with self.make(root) as service:
                source = Source.file(self.file(service,root))
                job = service.submit(OWNER,[source],revision({'delay':30,'ignore_cancel':True,'spawn_child':True}),idempotency_key='block')[0]
                detail = wait_for(service,job,{'running'})
                slot = service._slots[PipelineStage.SUMMARIZE]
                old_command = slot['command']
                old_generation = slot['generation']
                deadline = time.monotonic()+3
                marker = Path(old_command.output_dir)/'child.pid'
                while not marker.exists() and time.monotonic()<deadline:
                    time.sleep(0.02)
                child_pid = int(marker.read_text())
                service.cancel(OWNER,job,detail['current_attempt_id'])
                self.assertEqual(wait_for(service,job,{'cancelled'})['status'],'cancelled')
                new_slot = service._slots[PipelineStage.SUMMARIZE]
                self.assertNotEqual(new_slot['generation'],old_generation)
                self.assertFalse(service._finish(StageResult(old_command.token,'fake','summary'),new_slot))
                if os.name != 'nt':
                    stat = Path(f'/proc/{child_pid}/stat')
                    self.assertTrue(not stat.exists() or stat.read_text().split()[2] == 'Z')
                self.assertFalse(marker.exists())

    def test_failure_retry_preserves_settings_and_secret_versions(self):
        with tempfile.TemporaryDirectory() as root:
            with self.make(root) as service:
                secret = service.secrets.put('local','openai','original-secret')
                settings = revision({'fail_stage':4}, {'summary_api_key':secret})
                job = service.submit(OWNER,[Source.file(self.file(service,root))],settings,idempotency_key='fail')[0]
                detail = wait_for(service,job,{'failed'})
                self.assertEqual(detail['attempts'][0]['error_code'],'stage_failed')
                public = json.dumps(service.list_jobs(OWNER))+json.dumps(service.events_since(OWNER))
                self.assertNotIn('original-secret',public)
                self.assertNotIn('sensitive.example',public)
                service.secrets.put('local','openai','replacement-secret')
                new_attempt = service.retry(OWNER,job,detail['current_attempt_id'],idempotency_key='again')
                again = wait_for(service,job,{'failed'})
                self.assertEqual(len(again['attempts']),2)
                stored = service.db.get('settings_revisions',settings.id)
                self.assertEqual(stored['secret_versions'],[['summary_api_key',secret]])
                service.secrets._store(secret).path.unlink()
                with self.assertRaises(ServiceError) as exc:
                    service.retry(OWNER,job,new_attempt,idempotency_key='missing')
                self.assertEqual(exc.exception.code,'credentials_missing')

    def test_recovery_and_exclusive_lock(self):
        with tempfile.TemporaryDirectory() as root:
            service = self.make(root)
            with self.assertRaises(RuntimeError):
                self.make(root)
            jobs = service.submit(OWNER,[Source.file(self.file(service,root))],revision(),idempotency_key='pending')
            orphan = Path(root)/'jobs'/'orphan.part'
            orphan.parent.mkdir(exist_ok=True)
            orphan.write_text('unfinished')
            service.close()
            with self.make(root) as restarted:
                self.assertFalse(orphan.exists())
                self.assertEqual(wait_for(restarted,jobs[0],{'completed'})['status'],'completed')

    @unittest.skipIf(os.name=='nt','SIGKILL server crash test requires Unix')
    def test_server_crash_interrupted_and_queued_restore(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = multiprocessing.get_context('spawn')
            connection, child = ctx.Pipe()
            server = ctx.Process(target=crash_server,args=(root,child))
            server.start()
            child.close()
            try:
                self.assertTrue(connection.poll(10))
                jobs, worker_pids = connection.recv()
                server.kill()
                server.join(3)
                time.sleep(0.15)
                with self.make(root) as restarted:
                    self.assertEqual(restarted.detail(OWNER,jobs[0])['status'],'interrupted')
                    second = restarted.detail(OWNER,jobs[1])
                    self.assertIn(second['status'],{'queued','running'})
                    restarted.cancel(OWNER,jobs[1],second['current_attempt_id'])
                    wait_for(restarted,jobs[1],{'cancelled'})
                for pid in worker_pids:
                    stat = Path(f'/proc/{pid}/stat')
                    self.assertTrue(not stat.exists() or stat.read_text().split()[2]=='Z')
            finally:
                if server.is_alive():
                    server.kill()
                server.join(3)
                connection.close()

    def test_owner_limits_events_and_partial_result(self):
        with tempfile.TemporaryDirectory() as root:
            with self.make(root,event_limit=2) as service:
                job = service.submit(OWNER,[Source.file(self.file(service,root,'.mp4'))],revision(),end_stage=PipelineStage.CONVERT_AUDIO,idempotency_key='partial')[0]
                self.assertEqual(wait_for(service,job,{'completed'})['result_kind'],'stage_artifact')
                with self.assertRaises(ServiceError):
                    service.detail(UserContext('other'),job)
                self.assertEqual(service.list_jobs(UserContext('other'))['jobs'],[])
                service.prune_events()
                self.assertTrue(service.events_since(OWNER,1)['reset'])
                self.assertEqual(len(service.events_since(OWNER)['events']),2)

    def test_shutdown_preserves_pending_and_marks_running_interrupted(self):
        with tempfile.TemporaryDirectory() as root:
            service = self.make(root)
            service.start()
            source = Source.file(self.file(service,root))
            jobs = service.submit(OWNER,[source,source],revision({'delay':10}),idempotency_key='shutdown')
            wait_for(service,jobs[0],{'running'})
            service.close()
            restarted = self.make(root)
            try:
                self.assertEqual(restarted.detail(OWNER,jobs[0])['status'],'interrupted')
                self.assertEqual(restarted.detail(OWNER,jobs[1])['status'],'queued')
            finally:
                restarted.close()

if __name__ == '__main__':
    unittest.main()
