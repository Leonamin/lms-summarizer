import json
from pathlib import Path
import tempfile
import threading
import types
import unittest
from src.core.models.jobs import StageResult
from src.core.models.settings import SettingsRevision, UserContext
from src.core.models.stages import PipelineStage
from src.core.services.playback import PlaybackQueue
from src.video_pipeline.playback import classify_popup, play_to_end

OWNER = UserContext()


def revision():
    return SettingsRevision('rev-1', 'local', 'prompt', json.dumps({'student_id': '1'}), ())


class FakeDB:
    def __init__(self):
        self.events = []

    def event(self, *args, **kwargs):
        self.events.append((args, kwargs))


class FakeSlot(dict):
    def __init__(self):
        super().__init__(
            generation='gen-1',
            command=None,
            cancel=types.SimpleNamespace(clear=lambda: None),
            sent=[],
        )
        self['connection'] = types.SimpleNamespace(send=lambda command: self['sent'].append(command))


class FakeService:
    def __init__(self, root):
        self.paths = types.SimpleNamespace(file=lambda rel: Path(root) / rel,
                                           models=str(Path(root) / 'models'))
        self.lock = threading.RLock()
        self.changed = threading.Condition(self.lock)
        self.db = FakeDB()
        self.playback_timeout = 120
        self.submitted = []

    def _credentials(self, revision_dict):
        return {'lms_password': 'pw'}

    def submit(self, context, sources, revision_obj, end_stage=None, idempotency_key=None):
        self.submitted.append({'ref': sources[0].reference, 'end_stage': int(end_stage), 'key': idempotency_key})
        return ['job-1']


class ClassifyTests(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(classify_popup('이전에 시청했던 49:59부터 이어서 보시겠습니까? 예 아니오'), 'resume')
        self.assertEqual(classify_popup('본 콘텐츠의 진도체크를 시작합니다. ... 중단됩니다. 확인 취소'), 'simultaneous')
        self.assertEqual(classify_popup(''), 'other')


class PlayToEndTests(unittest.IsolatedAsyncioTestCase):
    async def noop_sleep(self, _seconds):
        return None

    async def test_completes_at_end(self):
        called = {'play': 0}

        async def click_play():
            called['play'] += 1

        async def read_confirm_text():
            return ''

        async def click_confirm():
            return None

        async def read_progress():
            return {'t': 10, 'dur': 10, 'paused': False}

        async def click_resume():
            return None

        result = await play_to_end(click_play=click_play, read_confirm_text=read_confirm_text,
                                   click_confirm=click_confirm, read_progress=read_progress,
                                   click_resume=click_resume, timeout=5, poll=1, sleep=self.noop_sleep)
        self.assertTrue(result['completed'])
        self.assertEqual(called['play'], 1)

    async def test_confirms_resume_popup(self):
        texts = ['이전에 시청했던 49:59부터 이어서 보시겠습니까? 예 아니오', '', '']
        confirms = {'n': 0}

        async def read_confirm_text():
            return texts.pop(0) if texts else ''

        async def click_confirm():
            confirms['n'] += 1

        result = await play_to_end(click_play=lambda: _none(), read_confirm_text=read_confirm_text,
                                   click_confirm=click_confirm,
                                   read_progress=lambda: _value({'t': 9, 'dur': 10, 'paused': False}),
                                   click_resume=lambda: _none(), timeout=5, poll=1, sleep=self.noop_sleep)
        self.assertTrue(result['completed'])
        self.assertEqual(result['popups'], ['resume'])
        self.assertEqual(confirms['n'], 1)

    async def test_pauses_after_three_popups(self):
        async def read_confirm_text():
            return '본 콘텐츠의 진도체크를 시작합니다. ... 확인 취소'

        result = await play_to_end(click_play=lambda: _none(), read_confirm_text=read_confirm_text,
                                   click_confirm=lambda: _none(),
                                   read_progress=lambda: _value({'t': 1, 'dur': 100, 'paused': False}),
                                   click_resume=lambda: _none(), timeout=30, poll=1, popup_limit=3,
                                   sleep=self.noop_sleep)
        self.assertFalse(result['completed'])
        self.assertEqual(result['reason'], 'popup_repeat')
        self.assertEqual(result['popup_repeats'], 3)

    async def test_times_out_without_progress(self):
        result = await play_to_end(click_play=lambda: _none(), read_confirm_text=lambda: _value(''),
                                   click_confirm=lambda: _none(),
                                   read_progress=lambda: _value({'t': 0, 'dur': 100, 'paused': False}),
                                   click_resume=lambda: _none(), timeout=2, poll=1, sleep=self.noop_sleep)
        self.assertFalse(result['completed'])
        self.assertEqual(result['reason'], 'playback_timeout')


async def _none():
    return None


async def _value(value):
    return value


class PlaybackQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.service = FakeService(self.tmp.name)
        self.queue = PlaybackQueue(self.service)

    def tearDown(self):
        self.tmp.cleanup()

    def submit(self, url='https://canvas/lecture/1', scope='download'):
        return self.queue.submit(OWNER, revision(), url, 'title', scope)

    def test_deduplicates_same_lecture(self):
        first = self.submit()
        second = self.submit()
        self.assertEqual(first['id'], second['id'])
        self.assertEqual(len(self.queue.list(OWNER)), 1)

    def test_dispatch_and_autosave_on_attendance(self):
        record = self.submit()
        slot = FakeSlot()
        self.assertTrue(self.queue.dispatch(slot))
        self.assertIsNotNone(slot['command'].playback)
        self.assertEqual(len(slot['sent']), 1)
        self.assertEqual(self.queue.get(OWNER, record['id'])['status'], 'running')

        result = StageResult(slot['command'].token, kind='playback',
                             data={'attended': True, 'popup_repeats': 1})
        self.queue.finish(slot['command'], result)
        stored = self.queue.get(OWNER, record['id'])
        self.assertEqual(stored['status'], 'completed')
        self.assertTrue(stored['attended'])
        self.assertEqual(self.service.submitted[0]['ref'], 'https://canvas/lecture/1')
        self.assertEqual(self.service.submitted[0]['end_stage'], int(PipelineStage.DOWNLOAD))
        self.assertEqual(self.service.submitted[0]['key'], 'autosave:https://canvas/lecture/1')

    def test_full_scope_uses_summarize(self):
        record = self.submit(scope='full')
        slot = FakeSlot()
        self.queue.dispatch(slot)
        self.queue.finish(slot['command'], StageResult(slot['command'].token, kind='playback', data={'attended': True}))
        self.assertEqual(self.service.submitted[0]['end_stage'], int(PipelineStage.SUMMARIZE))
        self.assertEqual(self.queue.get(OWNER, record['id'])['scope'], 'full')

    def test_popup_repeat_failure_is_flagged(self):
        record = self.submit()
        slot = FakeSlot()
        self.queue.dispatch(slot)
        self.queue.finish(slot['command'], StageResult(slot['command'].token, kind='playback',
                                                    error_code='popup_repeat', data={'popup_repeats': 3}))
        stored = self.queue.get(OWNER, record['id'])
        self.assertEqual(stored['status'], 'failed')
        self.assertEqual(stored['error_code'], 'popup_repeat')
        self.assertEqual(stored['popup_repeats'], 3)
        self.assertTrue(self.queue.popup_repeat_failed(OWNER))
        self.assertEqual(self.service.submitted, [])

    def test_recover_marks_running_interrupted(self):
        record = self.submit()
        state = self.queue.store.read()
        state['records'][record['id']]['status'] = 'running'
        self.queue.store.write(state)
        recovered = PlaybackQueue(self.service)
        self.assertEqual(recovered.get(OWNER, record['id'])['status'], 'interrupted')
        self.assertEqual(recovered.get(OWNER, record['id'])['error_code'], 'service_interrupted')


if __name__ == '__main__':
    unittest.main()
