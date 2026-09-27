from pathlib import Path
import sqlite3
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch

from src.core.models.jobs import Source, ServiceError
from src.core.models.stages import PipelineStage
from src.core.services.jobs import JobService
from test_job_service import FakeExecutor, OWNER, revision, wait_for

class FaultTests(unittest.TestCase):
    def make(self, root, **options):
        return JobService(Path(root), executor_factory=FakeExecutor,min_free_bytes=0,cancel_grace=0.05,shutdown_grace=0.1,**options)

    def source(self, service, root, suffix='.txt'):
        path=Path(root)/('source'+suffix)
        path.write_text('original')
        return Source.file(service.import_file(OWNER,path))

    def test_stage_transition_transaction_rollback_and_orphan_recovery(self):
        with tempfile.TemporaryDirectory() as root:
            service=self.make(root)
            job=service.submit(OWNER,[self.source(service,root,'.mp4')],revision(),idempotency_key='transaction')[0]
            slot={'generation':'test','cancel':threading.Event(),'command':None,'connection':types.SimpleNamespace(send=lambda _:None)}
            with service.lock:
                service._dispatch(PipelineStage.CONVERT_AUDIO,slot)
                result=FakeExecutor().execute(slot['command'],threading.Event())
                service.db.execute("CREATE TRIGGER fail_next BEFORE INSERT ON stage_runs WHEN NEW.stage=3 BEGIN SELECT RAISE(ABORT,'simulated failure'); END;")
                with self.assertRaises(sqlite3.IntegrityError):
                    service._finish(result,slot)
                detail=service.detail(OWNER,job)
                self.assertEqual(detail['status'],'running')
                self.assertEqual(len(detail['attempts'][0]['stages']),1)
                self.assertEqual(len(detail['artifacts']),1)  # Only input, no committed output.
                self.assertTrue((Path(slot['command'].output_dir).parent/'complete').exists())
                service.db.execute('DROP TRIGGER fail_next')
            service.close()
            with self.make(root) as restarted:
                self.assertEqual(restarted.detail(OWNER,job)['status'],'interrupted')
                self.assertFalse((Path(slot['command'].output_dir).parent/'complete').exists())

    def test_worker_exit_and_timeout_release_slot_for_next_job(self):
        with tempfile.TemporaryDirectory() as root:
            with self.make(root,stage_timeout=0.15) as service:
                source=self.source(service,root)
                slow=service.submit(OWNER,[source],revision({'delay':30,'ignore_cancel':True}),idempotency_key='slow')[0]
                wait_for(service,slow,{'running'})
                fast=service.submit(OWNER,[source],revision({'delay':0.01}),idempotency_key='fast')[0]
                self.assertEqual(wait_for(service,slow,{'failed'})['attempts'][0]['error_code'],'stage_timeout')
                wait_for(service,fast,{'completed'})
                crashed=service.submit(OWNER,[source],revision({'delay':30}),idempotency_key='crash')[0]
                wait_for(service,crashed,{'running'})
                service._slots[PipelineStage.SUMMARIZE]['process'].kill()
                self.assertEqual(wait_for(service,crashed,{'failed'})['attempts'][0]['error_code'],'worker_exited')

    def test_shared_inputs_preserved_for_failed_job_and_original_not_deleted(self):
        with tempfile.TemporaryDirectory() as root:
            with self.make(root) as service:
                source=self.source(service,root,'.wav')
                failed=service.submit(OWNER,[source],revision({'fail_stage':4}),idempotency_key='failed')[0]
                successful=service.submit(OWNER,[source],revision(),idempotency_key='success')[0]
                wait_for(service,failed,{'failed'})
                wait_for(service,successful,{'completed'})
                self.assertTrue(service.artifact_path(OWNER,source.reference).exists())
                self.assertEqual((Path(root)/'source.wav').read_text(),'original')
                old=service.detail(OWNER,failed)['current_attempt_id']
                service.retry(OWNER,failed,old,idempotency_key='retry')
                wait_for(service,failed,{'failed'})

    def test_cancel_all_only_snapshot_and_subscriber_disconnect(self):
        with tempfile.TemporaryDirectory() as root:
            with self.make(root) as service:
                source=self.source(service,root)
                jobs=service.submit(OWNER,[source,source],revision({'delay':1}),idempotency_key='old')
                wait_for(service,jobs[0],{'running'})
                events=service.subscribe(OWNER)
                next(events)
                events.close()
                self.assertCountEqual(service.cancel_all(OWNER),jobs)
                fresh=service.submit(OWNER,[source],revision(),idempotency_key='new')[0]
                for job in jobs:
                    wait_for(service,job,{'cancelled'})
                wait_for(service,fresh,{'completed'})
                self.assertEqual(service.stage_counts(OWNER)[4],{'queued':0,'running':0})

    def test_event_pagination_has_no_gaps(self):
        with tempfile.TemporaryDirectory() as root:
            with self.make(root) as service:
                job=service.submit(OWNER,[self.source(service,root)],revision(),idempotency_key='events')[0]
                wait_for(service,job,{'completed'})
                all_events=service.events_since(OWNER)['events']
                pages=[]; cursor=0
                while True:
                    batch=service.events_since(OWNER,cursor,limit=2)
                    if not batch['events']:
                        break
                    pages.extend(batch['events']); cursor=batch['cursor']
                self.assertEqual(pages,all_events)

    def test_disk_capacity_missing_input_and_secret_reference(self):
        with tempfile.TemporaryDirectory() as root:
            service=self.make(root,max_active=1)
            source=self.source(service,root)
            secret=service.secrets.put('local','openai','value')
            job=service.submit(OWNER,[source],revision(secrets={'summary_api_key':secret}),idempotency_key='one')[0]
            with self.assertRaises(ServiceError) as exc:
                service.submit(OWNER,[source],revision(),idempotency_key='two')
            self.assertEqual(exc.exception.code,'queue_full')
            with self.assertRaises(ServiceError) as exc:
                service.delete_secret(OWNER,secret)
            self.assertEqual(exc.exception.code,'secret_in_use')
            self.assertEqual(service.secret_usage(OWNER,secret),[job])
            old=service.detail(OWNER,job)['current_attempt_id']
            service.cancel(OWNER,job,old)
            service.artifact_path(OWNER,source.reference).unlink()
            with self.assertRaises(ServiceError) as exc:
                service.retry(OWNER,job,old,idempotency_key='missing')
            self.assertEqual(exc.exception.code,'input_missing')
            unused=self.source(service,root,'.wav')
            service.collect_unused_inputs(max_age_hours=-1)
            self.assertEqual(service.db.get('artifacts',unused.reference)['state'],'deleted')
            service.close()

    def test_disk_pressure_pauses_stage_without_losing_queue(self):
        with tempfile.TemporaryDirectory() as root:
            with self.make(root) as service:
                source=self.source(service,root)
                service.min_free_bytes=10**30
                job=service.submit(OWNER,[source],revision(),idempotency_key='disk')[0]
                time.sleep(0.15)
                self.assertEqual(service.detail(OWNER,job)['status'],'queued')
                service.min_free_bytes=0
                wait_for(service,job,{'completed'})

if __name__=='__main__':
    unittest.main()
