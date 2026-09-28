"""Durable account-scoped LMS queries scheduled in the download worker slot."""
import asyncio
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import uuid4
from src.core.models.jobs import ServiceError, StageCommand, StageResult, WorkToken
from src.core.models.stages import PipelineStage
from src.core.repositories.json_store import JsonStore
from src.core.repositories.jobs import utcnow

class CourseQueries:
    def __init__(self, service):
        self.service = service
        self.store = JsonStore(service.paths.file('course-queries.json'), {'queries': {}, 'cache': {}})
        self.recover()

    def recover(self):
        state = self.store.read()
        for query in state['queries'].values():
            if query['status'] == 'running':
                query.update(status='interrupted', error_code='service_interrupted', ended_at=utcnow())
        self.store.write(state)

    @staticmethod
    def account(revision):
        values = json.loads(revision.settings_json)
        # Password replacement invalidates the account cache as well.
        return sha256(json.dumps([revision.owner_id, values.get('student_id'), dict(revision.secret_versions).get('lms_password')]).encode()).hexdigest()

    @staticmethod
    def public(query):
        return {key: query[key] for key in ('id', 'course_id', 'status', 'created_at', 'ended_at', 'error_code')}

    def cached(self, revision, course_id=None):
        state = self.store.read()
        account = self.account(revision)
        record = state['cache'].get(account + ':' + (course_id or 'courses'))
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(record['time'])).total_seconds() if record else None
        pending = [self.public(q) for q in state['queries'].values() if q['account'] == account and q['course_id'] == course_id and q['status'] in ('queued', 'running')]
        return {'data': record['data'] if record and age < 86400 else ([] if not course_id else None),
                'cache_age_seconds': age, 'expired': age is None or age >= 86400,
                'refresh': pending[-1] if pending else None}

    def submit(self, context, revision, course_id=None):
        if revision.owner_id != context.owner_id:
            raise ServiceError('not_found')
        values = json.loads(revision.settings_json)
        credentials = self.service._credentials(asdict(revision))
        if not values.get('student_id') or not credentials.get('lms_password'):
            raise ServiceError('credentials_missing')
        state = self.store.read()
        account = self.account(revision)
        active = [q for q in state['queries'].values() if q['status'] in ('queued','running')]
        for query in active:
            if query['account'] == account and query['course_id'] == course_id:
                return self.public(query)
        if len(active) >= 20:
            raise ServiceError('queue_full')
        course = None
        if course_id:
            record = state['cache'].get(account + ':courses')
            course = next((c for c in (record['data'] if record else []) if c['id'] == course_id), None)
            if not course:
                raise ServiceError('not_found')
        query = {'id': str(uuid4()), 'owner_id': context.owner_id, 'account': account, 'course_id': course_id,
                 'course': course, 'revision': asdict(revision), 'status': 'queued', 'created_at': utcnow(),
                 'ended_at': None, 'error_code': None}
        state['queries'][query['id']] = query
        self.store.write(state)
        self.service.changed.notify_all()
        return self.public(query)

    def get(self, context, query_id):
        query = self.store.read()['queries'].get(query_id)
        if not query or query['owner_id'] != context.owner_id:
            raise ServiceError('not_found')
        return self.public(query)

    def dispatch(self, slot):
        state = self.store.read()
        query = next((q for q in state['queries'].values() if q['status'] == 'queued'), None)
        if not query:
            return False
        try:
            credentials = self.service._credentials(query['revision'])
        except ServiceError:
            query.update(status='failed', error_code='credentials_missing', ended_at=utcnow())
            self.store.write(state)
            return True
        token = WorkToken(query['id'], query['id'], query['id'], slot['generation'], PipelineStage.DOWNLOAD)
        command = StageCommand(token, '', '', query['revision']['settings_json'], '', credentials,
                               catalog_query={'course': query['course']})
        query['status'] = 'running'
        self.store.write(state)
        import time
        slot.update(command=command, started=time.monotonic(), cancel_deadline=None)
        slot['cancel'].clear()
        slot['connection'].send(command)
        return True

    def finish(self, command, result=None, code=None):
        state = self.store.read()
        query = state['queries'][command.token.job_id]
        error = code or (result.error_code if result else 'stage_failed')
        query.update(status=('interrupted' if error == 'service_interrupted' else 'failed') if error else 'completed',
                     error_code=error or None, ended_at=utcnow())
        if not error:
            state['cache'][query['account'] + ':' + (query['course_id'] or 'courses')] = {'time': utcnow(), 'data': result.data}
        self.store.write(state)
        self.service.db.event(query['owner_id'], None, 'course.updated', self.public(query))

    def uses_secret(self, owner, version):
        return any(q['owner_id'] == owner and q['status'] in ('queued','running') and
                   version in dict(q['revision']['secret_versions']).values() for q in self.store.read()['queries'].values())


def execute_query(command):
    from src.video_pipeline.course_scraper import CourseScraper
    from src.core.models.courses import Course
    values = json.loads(command.settings_json)
    password = command.credentials.get('lms_password')
    if not password or not values.get('student_id'):
        raise ServiceError('credentials_missing')
    async def fetch():
        scraper = CourseScraper(values['student_id'], password, chrome_path=values.get('chrome_path'), headless=values.get('headless',True))
        try:
            await scraper.start()
            course = command.catalog_query['course']
            if not course:
                return [c.to_dict() for c in await scraper.fetch_courses()]
            detail = await scraper.fetch_lectures(Course.from_dict(course))
            return {'course_name': detail.course_name, 'professors': detail.professors,
                    'weeks': [{'title': w.title, 'week_number': w.week_number,
                               'lectures': [{'title': l.title, 'url': l.full_url, 'duration': l.duration,
                                             'attendance': l.attendance, 'completion': l.completion,
                                             'is_video': l.is_video, 'is_upcoming': l.is_upcoming,
                                             'type': l.lecture_type.value} for l in w.lectures]} for w in detail.weeks]}
        finally:
            await scraper.close()
    return StageResult(command.token, kind='catalog', data=asyncio.run(fetch()))
