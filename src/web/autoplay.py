"""Auto-detect new LMS lecture videos and submit auto-save jobs (8-B, slice 1).

Reuses the durable course query queue and the job service. It never blocks on
another queue while holding a lock: each call performs one step (refresh the
course list, refresh one course, or submit detected videos) and returns, so the
periodic loop drives progress without a wait-graph.

Playback for attendance (Chrome/CDP) is intentionally not implemented here yet;
it needs the real LMS popup DOM investigation recorded in the 8-B plan.
"""
from datetime import datetime, timezone
from src.core.models.jobs import ServiceError
from src.core.models.settings import UserContext
from src.core.repositories.json_store import JsonStore
from src.core.services.detection import mark_seen, select_playback_videos

OWNER = UserContext()
DEFAULT_INTERVAL_MINUTES = 30


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_courses(value) -> list[str]:
    if isinstance(value, (list, tuple)):
        tokens = [str(item) for item in value]
    else:
        tokens = (value or '').replace(',', ' ').split()
    return [token for token in tokens if token.isdigit()]


class AutoDetect:
    def __init__(self, service, settings):
        self.service = service
        self.settings = settings
        self.store = JsonStore(service.paths.file('auto-play.json'),
                               {'seen': {}, 'submitted': {}, 'paused': False,
                                'last_run': None, 'last_error': None})

    # -- public surface ----------------------------------------------------
    def status(self) -> dict:
        state = self.store.read()
        config = self.settings.public()['settings']
        return {
            'enabled': bool(config.get('auto_detect_enabled')),
            'interval_minutes': config.get('auto_detect_interval_minutes') or DEFAULT_INTERVAL_MINUTES,
            'courses': parse_courses(config.get('auto_detect_courses')),
            'scope': config.get('auto_save_scope') or 'download',
            'paused': bool(state.get('paused')),
            'last_run': state.get('last_run'),
            'last_error': state.get('last_error'),
            'detected': len(state.get('seen', {})),
            'playing': len(self.service.playback.active(OWNER)),
        }

    def resume(self) -> dict:
        state = self.store.read()
        state['paused'] = False
        state['last_error'] = None
        self.store.write(state)
        return self.status()

    def tick(self, force: bool = False) -> dict:
        config = self.settings.public()['settings']
        state = self.store.read()
        if not force and not config.get('auto_detect_enabled'):
            return {'status': 'disabled'}
        if not force and state.get('paused'):
            return {'status': 'paused', 'reason': state.get('last_error')}
        # A playback that repeated a popup 3 times pauses auto-play (ADR-004).
        if not force and self.service.playback.popup_repeat_failed(OWNER):
            state['paused'] = True
            state['last_error'] = 'popup_repeat'
            self.store.write(state)
            return {'status': 'paused', 'reason': 'popup_repeat'}
        if not force and not self._due(state, config):
            return {'status': 'waiting'}
        courses = parse_courses(config.get('auto_detect_courses'))
        if not courses:
            return self._record(state, 'no_courses')
        try:
            revision = self.settings.snapshot(self.settings.public()['settings_revision'])
            return self._run(state, revision, courses, config)
        except ServiceError as error:
            return self._record(state, error.code)
        except OSError:
            return self._record(state, 'storage_error')

    # -- internals ---------------------------------------------------------
    def _due(self, state, config) -> bool:
        last = state.get('last_run')
        if not last:
            return True
        interval = config.get('auto_detect_interval_minutes') or DEFAULT_INTERVAL_MINUTES
        try:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds()
        except ValueError:
            return True
        return age >= interval * 60

    def _refresh(self, course_id, revision) -> None:
        with self.service.lock:
            self.service._ensure_open()
            self.service.courses.submit(OWNER, revision, course_id)

    def _run(self, state, revision, courses, config) -> dict:
        with self.service.lock:
            listing = self.service.courses.cached(revision)
        data = listing.get('data') or []
        if listing.get('expired') or not data:
            self._refresh(None, revision)
            return {'status': 'refreshing_courses'}
        known = {course.get('id') for course in data}
        course_names = {course.get('id'): course.get('long_name') for course in data}
        selected = [course_id for course_id in courses if course_id in known] or courses
        # Refresh course details one at a time before detecting.
        for course_id in selected:
            with self.service.lock:
                cache = self.service.courses.cached(revision, course_id)
            if cache.get('expired') or not cache.get('data'):
                self._refresh(course_id, revision)
                return {'status': 'refreshing_course', 'course_id': course_id}
        queued: list[str] = []
        for course_id in selected:
            with self.service.lock:
                cache = self.service.courses.cached(revision, course_id)
            detail = cache.get('data') or {}
            course_name = detail.get('course_name') or course_names.get(course_id)
            for week in detail.get('weeks') or []:
                for lecture in select_playback_videos(state['seen'], week.get('lectures', [])):
                    key = lecture.get('url') or lecture.get('title')
                    try:
                        record = self.service.playback.submit(
                            OWNER, revision, lecture['url'], lecture.get('title', ''),
                            config.get('auto_save_scope') or 'download',
                            course_name=course_name, week_title=week.get('title'))
                    except ServiceError as error:
                        return self._record(state, error.code, queued)
                    mark_seen(state['seen'], [lecture])
                    state['submitted'][key] = [record['id']]
                    queued.append(record['id'])
        return self._record(state, None, queued, completed=True)

    def _record(self, state, error, submitted=None, completed=False) -> dict:
        state['last_error'] = error
        if completed:
            state['last_run'] = _now()
        self.store.write(state)
        return {'status': 'error' if error else 'ok', 'error': error, 'submitted': submitted or []}
