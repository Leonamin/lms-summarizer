"""Framework-independent durable job service and single-process supervisor.

Public methods use owner contexts and IDs. Paths and secrets remain internal.
"""
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import errno
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import threading
import time
from urllib.parse import urlparse
from uuid import uuid4

from src.core.models.jobs import Source, WorkToken, StageCommand, StageResult, ServiceError
from src.core.models.settings import SettingsRevision, UserContext
from src.core.models.stages import PipelineStage
from src.core.repositories.jobs import JobRepository, utcnow
from src.core.repositories.paths import DataPaths
from src.core.repositories.secrets import SecretRepository
from src.core.runtime.executor import PipelineExecutor
from src.core.runtime.processes import DataLock, CancellationFlag, descendant_snapshot, reap
from src.core.runtime.worker import worker_main
from src.core.validation import initial_stage, validate_stage_range

ACTIVE = {'queued', 'running', 'cancelling'}
RETRYABLE = {'failed', 'cancelled', 'interrupted'}

# Code-specific messages shown in the UI instead of the generic status message.
STAGE_ERROR_MESSAGES = {
    'ai_unavailable': '요약 AI가 일시적으로 응답하지 않습니다. 잠시 후 다시 시도해 주세요.',
    'ai_quota': '요약 AI 사용 한도를 초과했습니다. 결제·한도를 확인해 주세요.',
    'ai_auth': '요약 AI 인증에 실패했습니다. API 키를 확인해 주세요.',
    'ai_timeout': '요약 AI 응답이 지연되었습니다. 잠시 후 다시 시도해 주세요.',
}

class JobService:
    def __init__(self, root: Path, *, executor_factory=PipelineExecutor, models_dir: Path = None,
                 min_free_bytes=2 * 1024**3, max_active=200, max_batch=50,
                 max_input_bytes=4 * 1024**3, cancel_grace=5, shutdown_grace=10,
                 stage_timeout=1800, playback_timeout=3 * 3600, poll_interval=0.05, event_days=7, event_limit=100000, worker_start_timeout=30):
        self.paths = DataPaths(Path(root).resolve(), Path(models_dir).resolve() if models_dir else Path(root).resolve() / 'models')
        self.lock = threading.RLock()
        self.changed = threading.Condition(self.lock)
        self.executor_factory = executor_factory
        self.min_free_bytes, self.max_active, self.max_batch = min_free_bytes, max_active, max_batch
        self.max_input_bytes = max_input_bytes
        self.cancel_grace, self.shutdown_grace = cancel_grace, shutdown_grace
        self.stage_timeout, self.poll_interval = stage_timeout, poll_interval
        self.playback_timeout = playback_timeout
        self.worker_start_timeout = worker_start_timeout
        self._startup_failures = {stage:0 for stage in PipelineStage}
        self.event_days, self.event_limit = event_days, event_limit
        self._ctx = multiprocessing.get_context('spawn')
        self._slots = {}
        self._catalog_turn = True
        self._thread = None
        self._stopping = False
        self._closed = False
        self._fatal = None
        self._last_maintenance = time.monotonic()
        self._data_lock = DataLock(self.paths.root)
        try:
            self.db = JobRepository(self.paths.file('jobs.sqlite3'))
            self.secrets = SecretRepository(self.paths.file('secrets'))
            self._recover()
            from src.core.services.courses import CourseQueries
            self.courses = CourseQueries(self)
            from src.core.services.playback import PlaybackQueue
            self.playback = PlaybackQueue(self)
            self._collect_files()
        except BaseException:
            if hasattr(self, 'db'):
                self.db.close()
            self._data_lock.close()
            raise

    def _ensure_open(self):
        if self._closed or self._stopping or self._fatal:
            raise ServiceError('service_unavailable')

    def _job(self, context, job_id):
        job = self.db.get('jobs', job_id)
        if not job or job['owner_id'] != context.owner_id:
            raise ServiceError('not_found')
        return job

    def _artifact(self, context, artifact_id):
        artifact = self.db.get('artifacts', artifact_id)
        if not artifact or artifact['owner_id'] != context.owner_id:
            raise ServiceError('not_found')
        return artifact

    def _event(self, job, kind='job.updated', **extra):
        self.db.event(job['owner_id'], job['id'], kind,
                      {'job_id': job['id'], 'attempt_id': job['current_attempt_id'],
                       'revision': job['revision'], 'status': job['status'], **extra})

    def _write_job(self, job, attempt):
        job['revision'] += 1
        job['status'] = attempt['status']
        self.db.update('jobs', job, status=job['status'], current_attempt_id=job['current_attempt_id'], revision=job['revision'])
        self.db.update('attempts', attempt, status=attempt['status'])
        self._event(job)

    def _new_run(self, attempt, stage, input_id):
        run = {'id': str(uuid4()), 'attempt_id': attempt['id'], 'stage': int(stage),
               'status':'queued', 'input_id': input_id, 'output_id': None,
               'generation': None, 'queued_at': utcnow(), 'started_at': None, 'ended_at': None}
        self.db.insert('stage_runs', run, attempt_id=attempt['id'], stage=int(stage),
                       status='queued', input_id=input_id, output_id=None)
        return run

    def _new_attempt(self, job, number):
        return self._new_attempt_from(
            job, number, job['initial_stage'],
            job['source_reference'] if job['source_kind'] == 'file' else None)

    def _new_attempt_from(self, job, number, start_stage, input_id):
        attempt = {'id': str(uuid4()), 'job_id':job['id'], 'number':number, 'status':'queued',
                   'current_stage':int(start_stage), 'generation':str(uuid4()), 'cancel_requested_at':None,
                   'started_at':None, 'ended_at':None, 'error_code':None, 'safe_message':None}
        self.db.insert('attempts', attempt, job_id=job['id'], number=number, status='queued')
        self._new_run(attempt, start_stage, input_id)
        return attempt

    def import_file(self, context: UserContext, path: Path) -> str:
        """Copy desktop/upload input into managed storage; never delete client files."""
        with self.lock:
            self._ensure_open()
            path = Path(path)
            initial_stage(path.name)
            if not path.is_file():
                raise ServiceError('input_missing')
            if path.stat().st_size == 0:
                raise ServiceError('input_empty')
            if path.stat().st_size > self.max_input_bytes:
                raise ServiceError('input_too_large')
            if shutil.disk_usage(self.paths.root).free < self.min_free_bytes + path.stat().st_size:
                raise ServiceError('disk_full')
            artifact_id = str(uuid4())
            relative = f'inputs/{artifact_id}/input{path.suffix.lower()}'
            target = self.paths.file(relative)
            target.parent.mkdir(parents=True)
            partial = target.with_suffix(target.suffix + '.part')
            try:
                with path.open('rb') as source, partial.open('xb') as destination:
                    copied = 0
                    while chunk := source.read(1024 * 1024):
                        copied += len(chunk)
                        if copied > self.max_input_bytes:
                            raise ServiceError('input_too_large')
                        destination.write(chunk)
                    destination.flush()
                    os.fsync(destination.fileno())
                if path.suffix.lower() == '.txt':
                    partial.read_text(encoding='utf-8-sig')
                os.replace(partial, target)
                record = {'id':artifact_id, 'owner_id':context.owner_id, 'kind':'input',
                          'path':relative, 'display_name':path.name, 'size':target.stat().st_size,
                          'state':'complete', 'created_at':utcnow(), 'job_id':None, 'attempt_id':None}
                with self.db.transaction():
                    self.db.insert('artifacts', record, owner_id=context.owner_id, state='complete')
                return artifact_id
            except BaseException:
                shutil.rmtree(target.parent, ignore_errors=True)
                raise

    def delete_input(self, context: UserContext, artifact_id: str):
        """Remove only unused managed input; job/attempt history remains immutable."""
        with self.lock:
            self._ensure_open()
            artifact = self._artifact(context, artifact_id)
            if artifact['kind'] != 'input':
                raise ServiceError('not_found')
            jobs = self.db.records('SELECT payload FROM jobs WHERE owner_id=?', (context.owner_id,))
            if any(job['source_kind'] == 'file' and job['source_reference'] == artifact_id for job in jobs):
                raise ServiceError('input_in_use')
            path = self.paths.file(artifact['path'])
            path.unlink(missing_ok=True)
            with self.db.transaction():
                artifact['state'] = 'deleted'
                self.db.update('artifacts', artifact, state='deleted')

    def _dedup(self, context, operation, key, fingerprint):
        if not key:
            raise ServiceError('idempotency_key_required')
        row = self.db.execute('SELECT fingerprint,result FROM idempotency WHERE owner_id=? AND operation=? AND key=?',
                              (context.owner_id, operation, key)).fetchone()
        if row:
            if row['fingerprint'] != fingerprint:
                raise ServiceError('idempotency_conflict')
            return json.loads(row['result'])
        return None

    def _remember(self, context, operation, key, fingerprint, result):
        self.db.execute('INSERT INTO idempotency VALUES(?,?,?,?,?)',
                         (context.owner_id, operation, key, fingerprint, json.dumps(result)))

    def submit(self, context: UserContext, sources: list[Source], revision: SettingsRevision,
               *, end_stage=PipelineStage.SUMMARIZE, idempotency_key: str) -> list[str]:
        with self.lock:
            self._ensure_open()
            if revision.owner_id != context.owner_id:
                raise ServiceError('not_found')
            fingerprint = hashlib.sha256(json.dumps([asdict(s) for s in sources] + [asdict(revision), int(end_stage)], sort_keys=True).encode()).hexdigest()
            existing = self._dedup(context, 'submit', idempotency_key, fingerprint)
            if existing is not None:
                return existing
            if not sources or len(sources) > self.max_batch:
                raise ServiceError('batch_limit')
            count = self.db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running','cancelling')").fetchone()[0]
            if count + len(sources) > self.max_active:
                raise ServiceError('queue_full')
            settings = json.loads(revision.settings_json)
            from src.core.models.settings import PromptSettings
            from src.core.services.settings import snapshot_settings
            snapshot_settings(context.owner_id, settings, PromptSettings(mode='custom', custom_prompt=revision.resolved_prompt), dict(revision.secret_versions))
            prepared = []
            for source in sources:
                if source.kind == 'file':
                    artifact = self._artifact(context, source.reference)
                    if artifact['state'] != 'complete' or not self.paths.file(artifact['path']).is_file():
                        raise ServiceError('input_missing')
                    start = initial_stage(artifact['display_name'])
                    name = artifact['display_name']
                elif source.kind == 'url':
                    url = urlparse(source.reference)
                    if url.scheme != 'https' or url.hostname != 'canvas.ssu.ac.kr' or not url.path.startswith('/courses/') or url.username or url.password:
                        raise ServiceError('invalid_url')
                    start, name = PipelineStage.DOWNLOAD, source.display_name or 'LMS lecture'
                else:
                    raise ServiceError('invalid_source')
                validate_stage_range(start, end_stage)
                prepared.append((source, start, name))
            result = []
            with self.db.transaction():
                saved = self.db.get('settings_revisions', revision.id)
                record = asdict(revision)
                if saved and saved != json.loads(json.dumps(record)):
                    raise ServiceError('settings_conflict')
                if not saved:
                    self.db.insert('settings_revisions', record, owner_id=context.owner_id)
                for source, start, name in prepared:
                    job = {'id':str(uuid4()), 'owner_id':context.owner_id, 'source_kind':source.kind,
                           'source_reference':source.reference, 'display_name':name,
                           'course_name':source.course_name, 'week_title':source.week_title,
                           'initial_stage':int(start), 'end_stage':int(end_stage),
                           'settings_revision_id':revision.id, 'current_attempt_id':'',
                           'status':'queued', 'revision':1, 'created_at':utcnow(), 'result_kind':None,
                           'keep_source':bool(settings.get('keep_source', False)),
                           'keep_audio':bool(settings.get('keep_audio', False))}
                    self.db.insert('jobs', job, owner_id=context.owner_id, status='queued', current_attempt_id='', revision=1)
                    attempt = self._new_attempt(job, 1)
                    job['current_attempt_id'] = attempt['id']
                    self.db.update('jobs', job, current_attempt_id=attempt['id'])
                    self._event(job)
                    result.append(job['id'])
                self._remember(context, 'submit', idempotency_key, fingerprint, result)
            self.changed.notify_all()
            return result

    def _terminal(self, job, attempt, status, code=None):
        attempt.update(status=status, ended_at=utcnow(), error_code=code,
                       safe_message=STAGE_ERROR_MESSAGES.get(code) or {
                           'cancelled':'작업이 취소되었습니다.', 'interrupted':'실행이 중단되었습니다.',
                           'failed':'작업 실행에 실패했습니다.'}.get(status))
        for run in self.db.records("SELECT payload FROM stage_runs WHERE attempt_id=? AND status IN ('queued','running')", (attempt['id'],)):
            run.update(status='failed', ended_at=utcnow(), error_code=code or status)
            self.db.update('stage_runs', run, status='failed')
            self._event(job, 'stage.updated', stage=run['stage'], stage_status='failed', reason=code or status)
        self._write_job(job, attempt)

    def cancel(self, context: UserContext, job_id: str, attempt_id: str):
        with self.lock:
            self._ensure_open()
            job = self._job(context, job_id)
            if job['current_attempt_id'] != attempt_id:
                raise ServiceError('attempt_conflict')
            if job['status'] not in ACTIVE:
                return self.detail(context, job_id)
            attempt = self.db.get('attempts', attempt_id)
            with self.db.transaction():
                attempt['cancel_requested_at'] = utcnow()
                if job['status'] == 'queued':
                    self._terminal(job, attempt, 'cancelled', 'cancelled')
                elif job['status'] == 'running':
                    attempt['status'] = 'cancelling'
                    self._write_job(job, attempt)
            for slot in self._slots.values():
                command = slot['command']
                if command and command.token.attempt_id == attempt_id:
                    slot['cancel'].set()
                    slot['cancel_deadline'] = slot['cancel_deadline'] or time.monotonic() + self.cancel_grace
            self.changed.notify_all()
            return self.detail(context, job_id)

    def cancel_all(self, context: UserContext):
        with self.lock:
            snapshot = [(j['id'], j['current_attempt_id']) for j in self.db.records("SELECT payload FROM jobs WHERE owner_id=? AND status IN ('queued','running','cancelling')", (context.owner_id,))]
            for job_id, attempt_id in snapshot:
                self.cancel(context, job_id, attempt_id)
            return [job_id for job_id, _ in snapshot]

    def retry(self, context: UserContext, job_id: str, attempt_id: str, *, idempotency_key: str,
              settings_revision=None):
        with self.lock:
            self._ensure_open()
            job = self._job(context, job_id)
            operation = f'retry:{job_id}'
            adopted = settings_revision is not None
            revision = self._revision_for_attempt(context, job, settings_revision)
            # Fingerprint the chosen revision so a replay with different settings conflicts.
            fingerprint = f'{attempt_id}:{revision["id"]}'
            prior = self._dedup(context, operation, idempotency_key, fingerprint)
            if prior is not None:
                return prior
            if job['current_attempt_id'] != attempt_id or job['status'] not in RETRYABLE:
                raise ServiceError('attempt_conflict')
            if job['source_kind'] == 'file':
                artifact = self._artifact(context, job['source_reference'])
                if artifact['state'] != 'complete' or not self.paths.file(artifact['path']).is_file():
                    raise ServiceError('input_missing')
            active = self.db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running','cancelling')").fetchone()[0]
            if active >= self.max_active:
                raise ServiceError('queue_full')
            self._credentials(revision)  # Missing original secret versions fail before creating an attempt.
            with self.db.transaction():
                self._save_revision(context, revision)
                number = self.db.execute('SELECT max(number) FROM attempts WHERE job_id=?', (job_id,)).fetchone()[0] + 1
                attempt = self._new_attempt(job, number)
                self._bind_revision(job, revision, adopted)
                job['current_attempt_id'] = attempt['id']
                job['result_kind'] = None
                self._write_job(job, attempt)
                self._remember(context, operation, idempotency_key, fingerprint, attempt['id'])
            self.changed.notify_all()
            return attempt['id']

    def resume(self, context: UserContext, job_id: str, attempt_id: str, *, idempotency_key: str,
               settings_revision=None):
        """Retry a failed/interrupted job from its last completed stage, reusing artifacts."""
        with self.lock:
            self._ensure_open()
            job = self._job(context, job_id)
            operation = f'resume:{job_id}'
            adopted = settings_revision is not None
            revision = self._revision_for_attempt(context, job, settings_revision)
            # Fingerprint the chosen revision so a replay with different settings conflicts.
            fingerprint = f'{attempt_id}:{revision["id"]}'
            prior = self._dedup(context, operation, idempotency_key, fingerprint)
            if prior is not None:
                return prior
            if job['current_attempt_id'] != attempt_id or job['status'] not in RETRYABLE:
                raise ServiceError('attempt_conflict')
            point = self._resume_point(job, job['end_stage'])
            if point is None:
                raise ServiceError('no_resume_point')
            start_stage, input_id = point
            active = self.db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running','cancelling')").fetchone()[0]
            if active >= self.max_active:
                raise ServiceError('queue_full')
            self._credentials(revision)
            with self.db.transaction():
                self._save_revision(context, revision)
                number = self.db.execute('SELECT max(number) FROM attempts WHERE job_id=?', (job_id,)).fetchone()[0] + 1
                attempt = self._new_attempt_from(job, number, start_stage, input_id)
                self._bind_revision(job, revision, adopted)
                job['current_attempt_id'] = attempt['id']
                job['result_kind'] = None
                self._write_job(job, attempt)
                self._remember(context, operation, idempotency_key, fingerprint, attempt['id'])
            self.changed.notify_all()
            return attempt['id']

    def _revision_for_attempt(self, context, job, settings_revision):
        """Choose the settings revision for a new attempt.

        Without ``settings_revision`` the job's frozen revision is reused unchanged.
        When the caller supplies one (the user chose to run with the current
        settings), it must be a SettingsRevision owned by the same context and it
        replaces the frozen revision for this attempt.
        """
        if settings_revision is None:
            revision = self.db.get('settings_revisions', job['settings_revision_id'])
            if not revision:
                raise ServiceError('settings_conflict')
            return revision
        if not isinstance(settings_revision, SettingsRevision):
            raise TypeError('settings_revision must be a SettingsRevision')
        if settings_revision.owner_id != context.owner_id:
            raise ServiceError('not_found')
        return asdict(settings_revision)

    def _save_revision(self, context, revision):
        saved = self.db.get('settings_revisions', revision['id'])
        if saved and saved != json.loads(json.dumps(revision)):
            raise ServiceError('settings_conflict')
        if not saved:
            self.db.insert('settings_revisions', revision, owner_id=context.owner_id)

    def _bind_revision(self, job, revision, adopted):
        """Point the job at the revision used for the next attempt.

        When adopting the current settings, retention flags travel with them so a
        retry does not silently keep the previous run's keep_source/keep_audio.
        """
        job['settings_revision_id'] = revision['id']
        if not adopted:
            return
        values = json.loads(revision['settings_json'])
        job['keep_source'] = bool(values.get('keep_source', False))
        job['keep_audio'] = bool(values.get('keep_audio', False))

    def _resume_point(self, job, end_stage):
        """Return (stage, artifact_id) to resume from, or None when nothing is resumable.

        Considers every attempt of the job (newest first), not just the current one,
        so a failed resume attempt can be resumed again from the last retained output.
        """
        end = int(end_stage)
        attempts = self.db.records('SELECT payload FROM attempts WHERE job_id=? ORDER BY number DESC', (job['id'],))
        for attempt in attempts:
            runs = self.db.records('SELECT payload FROM stage_runs WHERE attempt_id=?', (attempt['id'],))
            completed = sorted((run for run in runs if run['status'] == 'completed' and run['output_id']),
                               key=lambda run: run['stage'], reverse=True)
            for run in completed:
                if int(run['stage']) + 1 > end:
                    continue
                artifact = self.db.get('artifacts', run['output_id'])
                if artifact and artifact['state'] == 'complete' and self.paths.file(artifact['path']).is_file():
                    return int(run['stage']) + 1, run['output_id']
        return None

    def continue_job(self, context: UserContext, job_id: str, attempt_id: str, end_stage: int, *,
                     idempotency_key: str):
        """Extend a completed job to a later stage, reusing the last artifact."""
        with self.lock:
            self._ensure_open()
            job = self._job(context, job_id)
            target = int(end_stage)
            operation = f'continue:{job_id}'
            fingerprint = json.dumps([attempt_id, target], sort_keys=True)
            prior = self._dedup(context, operation, idempotency_key, fingerprint)
            if prior is not None:
                return prior
            if job['current_attempt_id'] != attempt_id or job['status'] != 'completed':
                raise ServiceError('attempt_conflict')
            if target not in (int(PipelineStage.CONVERT_AUDIO), int(PipelineStage.STT),
                              int(PipelineStage.SUMMARIZE)):
                raise ServiceError('invalid_stage')
            runs = self.db.records('SELECT payload FROM stage_runs WHERE attempt_id=?', (attempt_id,))
            completed = [run for run in runs if run['status'] == 'completed' and run['output_id']]
            if not completed:
                raise ServiceError('input_missing')
            last = max(completed, key=lambda run: run['stage'])
            if target <= last['stage']:
                raise ServiceError('invalid_stage')
            artifact = self.db.get('artifacts', last['output_id'])
            if not artifact or artifact['state'] != 'complete' or not self.paths.file(artifact['path']).is_file():
                raise ServiceError('input_missing')
            active = self.db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running','cancelling')").fetchone()[0]
            if active >= self.max_active:
                raise ServiceError('queue_full')
            revision = self.db.get('settings_revisions', job['settings_revision_id'])
            self._credentials(revision)
            with self.db.transaction():
                number = self.db.execute('SELECT max(number) FROM attempts WHERE job_id=?', (job_id,)).fetchone()[0] + 1
                attempt = self._new_attempt_from(job, number, last['stage'] + 1, last['output_id'])
                job['end_stage'] = target
                job['current_attempt_id'] = attempt['id']
                job['result_kind'] = None
                self._write_job(job, attempt)
                self._remember(context, operation, idempotency_key, fingerprint, attempt['id'])
            self.changed.notify_all()
            return attempt['id']

    def _credentials(self, revision):
        try:
            return {name:self.secrets.get(revision['owner_id'], version) for name, version in revision['secret_versions']}
        except (KeyError, ValueError, OSError):
            raise ServiceError('credentials_missing') from None

    def detail(self, context: UserContext, job_id: str):
        with self.lock:
            job = self._job(context, job_id)
            public = {key:job.get(key) for key in ('id','display_name','source_kind','initial_stage','end_stage','settings_revision_id','current_attempt_id','status','revision','created_at','result_kind','course_name','week_title')}
            attempts = self.db.records('SELECT payload FROM attempts WHERE job_id=? ORDER BY number', (job_id,))
            public['attempts'] = []
            artifact_ids = {job['source_reference']} if job['source_kind'] == 'file' else set()
            for attempt in attempts:
                runs = self.db.records('SELECT payload FROM stage_runs WHERE attempt_id=? ORDER BY stage', (attempt['id'],))
                public_attempt = {k:v for k,v in attempt.items() if k != 'generation'}
                public_attempt['stages'] = [{k:v for k,v in run.items() if k != 'generation'} for run in runs]
                artifact_ids.update(run['output_id'] for run in runs if run['output_id'])
                public['attempts'].append(public_attempt)
            public['artifacts'] = [self._public_artifact(self.db.get('artifacts', i)) for i in sorted(artifact_ids)]
            public['retryable'] = job['status'] in RETRYABLE
            return public

    @staticmethod
    def _public_artifact(artifact):
        return {k:artifact[k] for k in ('id','kind','display_name','size','state','job_id','attempt_id')}

    def list_jobs(self, context: UserContext, *, status=None, after=0, limit=50):
        with self.lock:
            limit = max(1, min(int(limit), 200))
            rows = self.db.execute('SELECT rowid,id FROM jobs WHERE owner_id=? AND rowid>? AND (? IS NULL OR status=?) ORDER BY rowid LIMIT ?',
                                   (context.owner_id, after, status, status, limit)).fetchall()
            sequence = self.db.execute("SELECT seq FROM sqlite_sequence WHERE name='events'").fetchone()
            cursor = sequence[0] if sequence else 0
            return {'jobs':[self.detail(context, r['id']) for r in rows],
                    'next_cursor':rows[-1]['rowid'] if rows else after, 'event_cursor':cursor}

    def logs(self, context, job_id, cursor=0, limit=100):
        with self.lock:
            self._job(context, job_id)
            rows = self.db.execute("SELECT seq,type,payload,timestamp FROM events WHERE owner_id=? AND job_id=? AND seq>? ORDER BY seq LIMIT ?",
                                   (context.owner_id, job_id, cursor, max(1,min(limit,200)))).fetchall()
            return {'logs': [{'seq': r['seq'], 'type': r['type'], 'timestamp': r['timestamp'], **json.loads(r['payload'])} for r in rows],
                    'next_cursor': rows[-1]['seq'] if rows else cursor}

    def artifact_path(self, context: UserContext, artifact_id: str) -> Path:
        with self.lock:
            artifact = self._artifact(context, artifact_id)
            if artifact['state'] != 'complete':
                raise ServiceError('artifact_missing')
            path = self.paths.file(artifact['path'])
            if not path.is_file():
                raise ServiceError('artifact_missing')
            return path

    def events_since(self, context: UserContext, cursor=0, limit=200):
        with self.lock:
            floor = self.db.execute('SELECT min(seq) FROM events').fetchone()[0]
            latest = self.db.execute("SELECT seq FROM sqlite_sequence WHERE name='events'").fetchone()
            latest = latest[0] if latest else 0
            reset = bool(cursor < 0 or cursor > latest or (floor and cursor and cursor < floor-1) or (not floor and cursor < latest))
            rows = [] if reset else self.db.execute('SELECT seq,job_id,type,payload,timestamp FROM events WHERE owner_id=? AND seq>? ORDER BY seq LIMIT ?',
                                                     (context.owner_id, cursor, max(1,min(limit,1000)))).fetchall()
            return {'reset':reset, 'events':[{**dict(r),'payload':json.loads(r['payload'])} for r in rows], 'cursor':rows[-1]['seq'] if rows else latest}

    def subscribe(self, context: UserContext, cursor=0, *, stop=None, heartbeat=15):
        """Pull persisted events without holding the supervisor lock while yielding."""
        while stop is None or not stop.is_set():
            with self.changed:
                if self._closed:
                    return
                batch = self.events_since(context, cursor)
                deadline = time.monotonic() + heartbeat
                while not batch['reset'] and not batch['events']:
                    if self._closed:
                        return
                    if stop is not None and stop.is_set():
                        return
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    self.changed.wait(timeout=remaining)
                    if self._closed:
                        return
                    batch = self.events_since(context, cursor)
            if batch['reset']:
                cursor = batch['cursor']
                yield {'type':'reset','seq':cursor}
            elif batch['events']:
                for event in batch['events']:
                    cursor = event['seq']
                    yield event
            else:
                yield {'type':'heartbeat','seq':cursor}

    def stage_counts(self, context: UserContext):
        with self.lock:
            rows = self.db.execute("SELECT s.stage,s.status,count(*) AS count FROM stage_runs s JOIN attempts a ON a.id=s.attempt_id JOIN jobs j ON j.id=a.job_id WHERE j.owner_id=? AND j.current_attempt_id=a.id AND s.status IN ('queued','running') GROUP BY s.stage,s.status", (context.owner_id,)).fetchall()
            result = {int(stage):{'queued':0,'running':0} for stage in PipelineStage}
            for row in rows:
                result[row['stage']][row['status']] = row['count']
            return result

    def start(self):
        with self.lock:
            self._ensure_open()
            if self._thread:
                return
            try:
                for stage in PipelineStage:
                    self._spawn(stage)
            except BaseException:
                for slot in self._slots.values():
                    self._dispose(slot)
                self._slots.clear()
                raise
            self._thread = threading.Thread(target=self._supervise, name='job-supervisor', daemon=True)
            self._thread.start()

    def _spawn(self, stage):
        connection, child = self._ctx.Pipe()
        lifetime_child, lifetime = self._ctx.Pipe(duplex=False)
        cancelled = CancellationFlag(self._ctx)
        process = self._ctx.Process(target=worker_main, args=(child,lifetime_child,cancelled,self.executor_factory), name=f'lms-stage-{int(stage)}')
        process.start()
        child.close()
        lifetime_child.close()
        slot = {'process':process,'connection':connection,'lifetime':lifetime,'cancel':cancelled,
                'generation':str(uuid4()),'command':None,'ready':False,'cancel_deadline':None,'started':None,'booted':time.monotonic(),'descendants':{}}
        self._slots[stage] = slot
        return slot

    def _dispose(self, slot):
        if slot.get('disposed'):
            return
        reap(slot['process'], tuple(slot['descendants'].values()))
        slot['connection'].close()
        slot['lifetime'].close()
        slot['process'].close()
        slot['disposed'] = True

    def _recover(self):
        with self.db.transaction():
            for job in self.db.records("SELECT payload FROM jobs WHERE status IN ('running','cancelling')"):
                attempt = self.db.get('attempts', job['current_attempt_id'])
                self._terminal(job, attempt, 'interrupted', 'service_interrupted')

    def _queued(self, stage):
        rows = self.db.records("SELECT s.payload FROM stage_runs s JOIN attempts a ON a.id=s.attempt_id JOIN jobs j ON j.id=a.job_id WHERE s.stage=? AND s.status='queued' AND a.status='queued' AND j.current_attempt_id=a.id ORDER BY s.rowid LIMIT 1", (int(stage),))
        return rows[0] if rows else None

    def _dispatch(self, stage, slot):
        if shutil.disk_usage(self.paths.root).free < self.min_free_bytes:
            return
        run = self._queued(stage)
        if stage == PipelineStage.DOWNLOAD and self.playback.dispatch(slot):
            return
        if stage == PipelineStage.DOWNLOAD and (self._catalog_turn or not run) and self.courses.dispatch(slot):
            self._catalog_turn = False
            return
        if not run:
            return
        attempt = self.db.get('attempts', run['attempt_id'])
        job = self.db.get('jobs', attempt['job_id'])
        revision = self.db.get('settings_revisions', job['settings_revision_id'])
        output = None
        try:
            credentials = self._credentials(revision)
            if run['input_id']:
                artifact = self.db.get('artifacts', run['input_id'])
                source = str(self.paths.file(artifact['path']))
                if artifact['state'] != 'complete' or not Path(source).is_file():
                    raise ServiceError('input_missing')
            else:
                source = job['source_reference']
            token = WorkToken(job['id'],attempt['id'],run['id'],slot['generation'],stage)
            output = self.paths.file(f"jobs/{job['id']}/{attempt['id']}/{run['id']}/.part")
            output.mkdir(parents=True, exist_ok=False)
            command = StageCommand(token, source, str(output), revision['settings_json'], revision['resolved_prompt'], credentials, str(self.paths.models))
        except (ServiceError, OSError) as exc:
            code = exc.code if isinstance(exc, ServiceError) else 'disk_full' if exc.errno == errno.ENOSPC else 'stage_failed'
            with self.db.transaction():
                self._terminal(job, attempt, 'failed', code)
            # A failed mkdir may have created some of the parent directories.
            if output is not None:
                shutil.rmtree(output.parent, ignore_errors=True)
            return
        with self.db.transaction():
            now = utcnow()
            run.update(status='running', generation=slot['generation'], started_at=now)
            self.db.update('stage_runs', run, status='running')
            attempt.update(status='running', current_stage=int(stage), started_at=attempt['started_at'] or now)
            self._write_job(job, attempt)
            self._event(job, 'stage.updated', stage=int(stage), stage_status='running')
            self._event(job, 'log', stage=int(stage), message='stage_started')
        if stage == PipelineStage.DOWNLOAD:
            self._catalog_turn = True
        slot.update(command=command,started=time.monotonic(),cancel_deadline=None)
        slot['cancel'].clear()
        slot['connection'].send(command)

    def _valid_result(self, result, slot):
        command = slot['command']
        if not command or result.token != command.token or result.token.generation != slot['generation']:
            return False
        job = self.db.get('jobs', result.token.job_id)
        run = self.db.get('stage_runs', result.token.run_id)
        return job and run and job['current_attempt_id'] == result.token.attempt_id and run['status'] == 'running' and run['generation'] == result.token.generation

    def _finish(self, result, slot):
        command = slot['command']
        if command and command.catalog_query is not None:
            if result.token != command.token:
                return False
            self.courses.finish(command, result)
            slot.update(command=None, cancel_deadline=None, started=None)
            return True
        if command and command.playback is not None:
            if result.token != command.token:
                return False
            self.playback.finish(command, result)
            slot.update(command=None, cancel_deadline=None, started=None, budget=None)
            return True
        if not self._valid_result(result, slot):
            return False
        token = result.token
        job = self.db.get('jobs', token.job_id)
        attempt = self.db.get('attempts', token.attempt_id)
        if job['status'] == 'cancelling':
            # Always reap the process tree before making this slot available again.
            self._dispose(slot)
            with self.db.transaction():
                self._terminal(job, attempt, 'cancelled', 'cancelled')
            self._discard(slot['command'])
            self._spawn(token.stage)
            self.changed.notify_all()
            return True
        if result.error_code:
            from src.core.runtime.worker import SAFE_ERRORS
            code = result.error_code if result.error_code in SAFE_ERRORS else 'stage_failed'
            with self.db.transaction():
                self._terminal(job, attempt, 'failed', code)
            self._discard(slot['command'])
        else:
            try:
                self._publish(result, slot, job, attempt)
            except OSError as exc:
                import errno
                with self.db.transaction():
                    self._terminal(job, attempt, 'failed', 'disk_full' if exc.errno == errno.ENOSPC else 'output_missing')
                self._discard(slot['command'])
        slot.update(command=None,cancel_deadline=None,started=None)
        if self.db.get('jobs',job['id'])['status'] == 'completed':
            try:
                self._apply_retention(job)
            except OSError:
                # Results are already committed. Retry file cleanup during recovery.
                pass
        self.changed.notify_all()
        return True

    def _publish(self, result, slot, job, attempt):
        source = Path(result.output).resolve() if result.output else None
        staging = Path(slot['command'].output_dir).resolve()
        if not source or not source.is_relative_to(staging) or not source.is_file() or source.stat().st_size == 0:
            with self.db.transaction():
                self._terminal(job, attempt, 'failed', 'output_missing')
            self._discard(slot['command'])
            return
        target_dir = staging.parent / 'complete'
        os.replace(staging, target_dir)
        target = target_dir / source.relative_to(staging)
        artifact = {'id':str(uuid4()), 'owner_id':job['owner_id'], 'kind':result.kind,
                    'path':str(target.relative_to(self.paths.root)), 'display_name':target.name,
                    'size':target.stat().st_size, 'state':'complete', 'created_at':utcnow(),
                    'job_id':job['id'], 'attempt_id':attempt['id']}
        run = self.db.get('stage_runs', result.token.run_id)
        with self.db.transaction():
            self.db.insert('artifacts', artifact, owner_id=job['owner_id'], state='complete')
            run.update(status='completed', output_id=artifact['id'], ended_at=utcnow())
            self.db.update('stage_runs', run, status='completed', output_id=artifact['id'])
            # Name a URL job after the downloaded lecture instead of "LMS lecture".
            if (run['stage'] == 1 and job['source_kind'] == 'url'
                    and job.get('display_name') in (None, '', 'LMS lecture')):
                stem = Path(artifact['display_name']).stem
                if stem:
                    job['display_name'] = stem
            if run['stage'] == job['end_stage']:
                attempt.update(status='completed', ended_at=utcnow())
                job['result_kind'] = 'manual_ready' if result.kind == 'prompt' else 'summary' if result.kind == 'summary' else 'stage_artifact'
            else:
                attempt.update(status='queued', current_stage=run['stage']+1)
                self._new_run(attempt, run['stage']+1, artifact['id'])
            self._write_job(job, attempt)
            self._event(job, 'stage.updated', stage=run['stage'], stage_status='completed')
            self._event(job, 'log', stage=run['stage'], message='stage_completed', model_reused=result.model_reused)

    def _apply_retention(self, job):
        # Completed attempt audio is disposable only when it is not the requested result.
        runs = self.db.records('SELECT payload FROM stage_runs WHERE attempt_id=?', (job['current_attempt_id'],))
        for run in runs:
            if run['output_id'] and run['stage'] < job['end_stage'] and run['stage'] in (1,2):
                artifact = self.db.get('artifacts', run['output_id'])
                # Video follows keep_source; converted audio follows keep_audio.
                keep = job.get('keep_audio', False) if artifact['kind'] == 'audio' else job.get('keep_source', False)
                if not keep:
                    self._delete_artifact(artifact)
        if job['source_kind'] == 'file' and not job['keep_source']:
            input_id = job['source_reference']
            references = [j for j in self.db.records('SELECT payload FROM jobs') if j['source_kind']=='file' and j['source_reference']==input_id]
            artifact = self.db.get('artifacts', input_id)
            if all(j['status']=='completed' and not j['keep_source'] for j in references) and not artifact['display_name'].lower().endswith('.txt'):
                self._delete_artifact(artifact)

    def _delete_artifact(self, artifact):
        if artifact['state'] == 'deleted':
            return
        # Mark unavailable before unlink; recovery finishes an interrupted deletion.
        with self.db.transaction():
            artifact['state'] = 'deleted'
            self.db.update('artifacts', artifact, state='deleted')
        self.paths.file(artifact['path']).unlink(missing_ok=True)

    def _collect_files(self):
        records = self.db.records('SELECT payload FROM artifacts')
        known = set()
        for artifact in records:
            path = self.paths.file(artifact['path'])
            if artifact['state'] == 'deleted':
                path.unlink(missing_ok=True)
            else:
                known.add(path)
        # Only sweep service-owned input/work directories, never arbitrary paths.
        for name in ('inputs','jobs'):
            directory = self.paths.file(name)
            if directory.exists():
                for path in directory.rglob('*'):
                    if path.is_file() and path.resolve() not in known:
                        path.unlink()
                for path in sorted(directory.rglob('*'), key=lambda p:len(p.parts), reverse=True):
                    if path.is_dir() and not any(path.iterdir()):
                        path.rmdir()
        for job in self.db.records("SELECT payload FROM jobs WHERE status='completed'"):
            self._apply_retention(job)

    def _abort_slot(self, stage, slot, status, code):
        command = slot['command']
        self._dispose(slot)
        if command and command.catalog_query is not None:
            self.courses.finish(command, code=code)
        elif command and command.playback is not None:
            self.playback.finish(command, code=code)
        elif command:
            job = self.db.get('jobs',command.token.job_id)
            attempt = self.db.get('attempts',command.token.attempt_id)
            with self.db.transaction():
                self._terminal(job, attempt, status, code)
        if command:
            self._discard(command)
        if not slot['ready']:
            self._startup_failures[stage] += 1
            if self._startup_failures[stage] >= 3:
                del self._slots[stage]
                raise RuntimeError('worker_start_failed')
        self._spawn(stage)
        self.changed.notify_all()

    def _discard(self, command):
        if command and command.catalog_query is None and command.playback is None:
            shutil.rmtree(Path(command.output_dir).parent, ignore_errors=True)

    def _tick(self):
        for stage in PipelineStage:
            slot = self._slots[stage]
            if os.name != 'nt':
                for process in descendant_snapshot(slot['process'].pid):
                    slot['descendants'][process.pid] = process
            try:
                while slot['connection'].poll():
                    kind, result = slot['connection'].recv()
                    if kind == 'ready':
                        slot['ready'] = True
                        self._startup_failures[stage] = 0
                    elif kind == 'result':
                        self._finish(result, slot)
                        if self._slots[stage] is not slot:
                            break
            except (EOFError, OSError):
                pass
            if self._slots[stage] is not slot:
                continue
            if not slot['process'].is_alive():
                status = 'cancelled' if slot['cancel_deadline'] else 'failed'
                self._abort_slot(stage, slot, status, 'cancelled' if status=='cancelled' else 'worker_exited')
            elif not slot['ready'] and time.monotonic()-slot['booted'] > self.worker_start_timeout:
                self._abort_slot(stage,slot,'failed','worker_start_failed')
            elif slot['command']:
                now = time.monotonic()
                if slot['cancel_deadline'] and now >= slot['cancel_deadline']:
                    self._abort_slot(stage, slot, 'cancelled', 'cancelled')
                elif now - slot['started'] >= (slot.get('budget') or self.stage_timeout):
                    if slot['cancel_deadline']:
                        self._abort_slot(stage, slot, 'cancelled', 'cancelled')
                    else:
                        self._abort_slot(stage, slot, 'failed', 'stage_timeout')
            elif slot['ready']:
                self._dispatch(stage, slot)

    def _supervise(self):
        try:
            while True:
                with self.changed:
                    if self._stopping:
                        return
                    self._tick()
                    if time.monotonic() - self._last_maintenance >= 60:
                        self.prune_events()
                        self.collect_unused_inputs()
                        self._last_maintenance = time.monotonic()
                    self.changed.notify_all()
                    self.changed.wait(timeout=self.poll_interval)
        except BaseException as exc:
            with self.changed:
                self._fatal = type(exc).__name__
                self._stopping = True
                for slot in self._slots.values():
                    self._dispose(slot)
                self._slots.clear()
                try:
                    self._recover()
                    self.courses.recover()
                    self._collect_files()
                except Exception:
                    pass  # Recovery runs again on the next startup if storage is unavailable.
                self.changed.notify_all()

    def health(self):
        with self.lock:
            return {'running':bool(self._thread and self._thread.is_alive()) and not self._stopping,
                    'closed':self._closed,'error_code':'supervisor_failed' if self._fatal else None,
                    'sqlite_version':__import__('sqlite3').sqlite_version}

    def secret_usage(self, context: UserContext, version: str):
        with self.lock:
            revision_ids = {r['id'] for r in self.db.records('SELECT payload FROM settings_revisions WHERE owner_id=?', (context.owner_id,))
                            if any(v == version for _, v in r['secret_versions'])}
            return [j['id'] for j in self.db.records('SELECT payload FROM jobs WHERE owner_id=?', (context.owner_id,))
                    if j['settings_revision_id'] in revision_ids]

    def delete_secret(self, context: UserContext, version: str, *, force=False):
        with self.lock:
            self._ensure_open()
            self.secrets.get(context.owner_id, version)
            affected = self.secret_usage(context, version)
            if (affected or self.courses.uses_secret(context.owner_id, version)) and not force:
                raise ServiceError('secret_in_use')
            self.secrets._store(version).path.unlink()
            return affected

    def collect_unused_inputs(self, max_age_hours=24):
        with self.lock:
            pinned = {j['source_reference'] for j in self.db.records('SELECT payload FROM jobs') if j['source_kind']=='file'}
            cutoff = (datetime.now(timezone.utc)-timedelta(hours=max_age_hours)).isoformat()
            for artifact in self.db.records("SELECT payload FROM artifacts WHERE state='complete'"):
                if artifact['kind']=='input' and artifact['id'] not in pinned and artifact['created_at'] < cutoff:
                    self._delete_artifact(artifact)

    def prune_events(self):
        with self.lock, self.db.transaction():
            cutoff = (datetime.now(timezone.utc)-timedelta(days=self.event_days)).isoformat()
            self.db.execute('DELETE FROM events WHERE timestamp<?', (cutoff,))
            self.db.execute('DELETE FROM events WHERE seq <= (SELECT coalesce(max(seq),0)-? FROM events)', (self.event_limit,))

    def close(self):
        with self.changed:
            if self._closed:
                return
            self._stopping = True
            self.changed.notify_all()
            for slot in self._slots.values():
                slot['cancel'].set()
        if self._thread:
            self._thread.join(timeout=self.shutdown_grace+3)
        deadline = time.monotonic()+self.shutdown_grace
        for slot in self._slots.values():
            if slot['process'].is_alive():
                try:
                    slot['connection'].send(None)
                except (OSError, EOFError):
                    pass
        while time.monotonic() < deadline and any(slot['process'].is_alive() for slot in self._slots.values()):
            time.sleep(0.02)
        with self.changed:
            try:
                for slot in self._slots.values():
                    self._dispose(slot)
                self._slots.clear()
                self._recover()
                self.courses.recover()
                self._collect_files()
                self.db.close()
            finally:
                self._closed = True
                self._data_lock.close()
                self.changed.notify_all()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.close()
