"""Durable attendance-playback queue dispatched through the download slot (8-B).

Playback shares the single Chrome/CDP slot with course queries and downloads and
runs to completion before releasing it. On confirmed attendance the queue submits
the auto-save job with a fixed scope (download / download+STT+summary).
"""
from dataclasses import asdict
import time
from uuid import uuid4

from src.core.models.jobs import ServiceError, Source, StageCommand, WorkToken
from src.core.models.settings import SettingsRevision, UserContext
from src.core.models.stages import PipelineStage
from src.core.repositories.json_store import JsonStore
from src.core.repositories.jobs import utcnow

END_STAGE = {'download': PipelineStage.DOWNLOAD, 'full': PipelineStage.SUMMARIZE}


class PlaybackQueue:
    def __init__(self, service):
        self.service = service
        self.store = JsonStore(service.paths.file('playback.json'), {'records': {}})
        self.recover()

    def recover(self):
        state = self.store.read()
        for record in state['records'].values():
            if record['status'] == 'running':
                record.update(status='interrupted', error_code='service_interrupted', ended_at=utcnow())
        self.store.write(state)

    @staticmethod
    def public(record):
        return {key: record.get(key) for key in (
            'id', 'lecture_url', 'title', 'course_name', 'week_title', 'status', 'attended',
            'scope', 'popup_repeats', 'created_at', 'ended_at', 'error_code', 'job_ids')}

    def submit(self, context, revision, lecture_url, title, scope='download',
               course_name=None, week_title=None):
        state = self.store.read()
        for record in state['records'].values():
            if (record['owner_id'] == context.owner_id and record['lecture_url'] == lecture_url
                    and record['status'] in ('queued', 'running', 'completed')):
                return self.public(record)
        record = {'id': str(uuid4()), 'owner_id': context.owner_id, 'lecture_url': lecture_url,
                  'title': title, 'course_name': course_name, 'week_title': week_title,
                  'scope': scope, 'end_stage': int(END_STAGE.get(scope, PipelineStage.DOWNLOAD)),
                  'revision': asdict(revision), 'status': 'queued', 'attended': False,
                  'popup_repeats': 0, 'created_at': utcnow(), 'ended_at': None, 'error_code': None,
                  'job_ids': []}
        state['records'][record['id']] = record
        self.store.write(state)
        with self.service.lock:
            self.service.changed.notify_all()
        return self.public(record)

    def get(self, context, record_id):
        record = self.store.read()['records'].get(record_id)
        if not record or record['owner_id'] != context.owner_id:
            raise ServiceError('not_found')
        return self.public(record)

    def list(self, context, limit=50):
        records = [record for record in self.store.read()['records'].values()
                   if record['owner_id'] == context.owner_id]
        records.sort(key=lambda record: record['created_at'])
        return [self.public(record) for record in records[-limit:]]

    def active(self, context):
        return [self.public(record) for record in self.store.read()['records'].values()
                if record['owner_id'] == context.owner_id and record['status'] in ('queued', 'running')]

    def find(self, context, lecture_url):
        """Latest record for a lecture URL (any status), or None."""
        records = [record for record in self.store.read()['records'].values()
                   if record['owner_id'] == context.owner_id and record['lecture_url'] == lecture_url]
        if not records:
            return None
        return self.public(max(records, key=lambda record: record['created_at']))

    def retry(self, context, record_id):
        """Re-queue an unattended failed/interrupted playback for another attempt."""
        with self.store.lock:
            state = self.store.read()
            record = state['records'].get(record_id)
            if not record or record['owner_id'] != context.owner_id:
                raise ServiceError('not_found')
            if record['status'] in ('queued', 'running'):
                return self.public(record)
            if record['status'] == 'completed' and record.get('attended'):
                raise ServiceError('already_attended')
            record.update(status='queued', attended=False, error_code=None,
                          ended_at=None, popup_repeats=0)
            self.store.write(state)
        with self.service.lock:
            self.service.changed.notify_all()
        return self.public(record)

    def popup_repeat_failed(self, context):
        return any(record['owner_id'] == context.owner_id and record['error_code'] == 'popup_repeat'
                   for record in self.store.read()['records'].values())

    def dispatch(self, slot):
        state = self.store.read()
        record = next((item for item in state['records'].values() if item['status'] == 'queued'), None)
        if not record:
            return False
        try:
            credentials = self.service._credentials(record['revision'])
        except ServiceError:
            record.update(status='failed', error_code='credentials_missing', ended_at=utcnow())
            self.store.write(state)
            return True
        token = WorkToken(record['id'], record['id'], record['id'], slot['generation'], PipelineStage.DOWNLOAD)
        command = StageCommand(token, record['lecture_url'], '', record['revision']['settings_json'], '',
                               credentials, str(self.service.paths.models),
                               playback={'play_timeout': self.service.playback_timeout})
        record['status'] = 'running'
        self.store.write(state)
        slot.update(command=command, started=time.monotonic(), cancel_deadline=None,
                    budget=self.service.playback_timeout)
        slot['cancel'].clear()
        slot['connection'].send(command)
        return True

    def finish(self, command, result=None, code=None):
        state = self.store.read()
        record = state['records'][command.token.job_id]
        data = (result.data if result else None) or {}
        error = code or (result.error_code if result else 'playback_failed')
        record['attended'] = bool(data.get('attended'))
        record['popup_repeats'] = int(data.get('popup_repeats', record.get('popup_repeats', 0)))
        record.update(status=('interrupted' if error == 'service_interrupted' else
                              'failed' if error else 'completed'),
                      error_code=error or None, ended_at=utcnow())
        self.store.write(state)
        self.service.db.event(record['owner_id'], None, 'playback.updated', self.public(record))
        if not error and record['attended']:
            self._auto_save(record)

    def _auto_save(self, record):
        revision = SettingsRevision(**record['revision'])
        try:
            source = Source.url(record['lecture_url'], display_name=record.get('title'),
                                course_name=record.get('course_name'), week_title=record.get('week_title'))
            ids = self.service.submit(UserContext(record['owner_id']), [source], revision,
                                      end_stage=PipelineStage(record['end_stage']),
                                      idempotency_key='autosave:' + record['lecture_url'])
        except ServiceError as exc:
            record['autosave_error'] = exc.code
            self.service.db.event(record['owner_id'], None, 'playback.updated', self.public(record))
            return
        with self.store.lock:
            latest = self.store.read()
            stored = latest['records'].get(record['id'])
            if stored is not None:
                stored['job_ids'] = ids
                self.store.write(latest)
        self.service.db.event(record['owner_id'], None, 'playback.updated', self.public(record))
