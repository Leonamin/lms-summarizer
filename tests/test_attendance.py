import unittest
from src.video_pipeline.attendance import (
    attendance_token,
    is_attended,
    verify_attendance,
)

NONE = {'cls': 'xnvc-progress-info-attendance-status', 'text': '출석 정보 없음'}
PRESENT = {'cls': 'xnvc-progress-info-attendance-status attendance', 'text': '출석'}
ABSENT = {'cls': 'xnvc-progress-info-attendance-status absent', 'text': '결석'}
LATE = {'cls': 'xnvc-progress-info-attendance-status late', 'text': '지각'}


class TokenTests(unittest.TestCase):
    def test_base_class_alone_is_not_attended(self):
        # The base class itself contains "attendance", so tokens must be split.
        self.assertIsNone(attendance_token(NONE))
        self.assertFalse(is_attended(NONE))

    def test_modifier_tokens(self):
        self.assertEqual(attendance_token(PRESENT), 'attendance')
        self.assertTrue(is_attended(PRESENT))
        self.assertEqual(attendance_token(ABSENT), 'absent')
        self.assertFalse(is_attended(ABSENT))
        self.assertFalse(is_attended(LATE))
        self.assertFalse(is_attended(None))


class VerifyAttendanceTests(unittest.IsolatedAsyncioTestCase):
    async def noop_sleep(self, _seconds):
        return None

    async def test_attends_on_first_attempt(self):
        clicks = {'n': 0}

        async def read_state():
            return PRESENT

        async def click():
            clicks['n'] += 1
            return True

        async def reload_page():
            raise AssertionError('should not reload')

        result = await verify_attendance(read_state, click, reload_page,
                                         timeout=1, poll=0.05, reloads=2, sleep=self.noop_sleep)
        self.assertTrue(result['attended'])
        self.assertEqual(result['attempt'], 1)
        self.assertEqual(clicks['n'], 1)

    async def test_timeout_reloads_then_attends(self):
        queue = [NONE, NONE]
        rounds = [[NONE, NONE], [PRESENT]]
        state = {'round': 0}
        reloads = {'n': 0}

        async def read_state():
            if queue:
                return queue.pop(0)
            return NONE

        async def click():
            return True

        async def reload_page():
            state['round'] += 1
            reloads['n'] += 1
            queue.extend(rounds[state['round']] if state['round'] < len(rounds) else [])

        result = await verify_attendance(read_state, click, reload_page,
                                         timeout=0.05, poll=0.02, reloads=2, sleep=self.noop_sleep)
        self.assertTrue(result['attended'])
        self.assertEqual(result['attempt'], 2)
        self.assertEqual(reloads['n'], 1)

    async def test_gives_up_after_reloads(self):
        async def read_state():
            return ABSENT

        async def click():
            return True

        reloads = {'n': 0}

        async def reload_page():
            reloads['n'] += 1

        result = await verify_attendance(read_state, click, reload_page,
                                         timeout=0.04, poll=0.02, reloads=1, sleep=self.noop_sleep)
        self.assertFalse(result['attended'])
        self.assertEqual(result['attempt'], 2)
        self.assertEqual(reloads['n'], 1)


if __name__ == '__main__':
    unittest.main()
