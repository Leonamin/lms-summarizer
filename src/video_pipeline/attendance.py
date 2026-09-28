"""Attendance verification for 8-B auto-play (task 2).

Confirmed on the real LMS (2026-09-28, see wiki/logs/2026-09-28-autoplay-dom-investigation.md):
- The status refresh button and attendance badge live in the outer LTI frame
  (`tool_content` = `learningx/.../lecture_attendance/items/view/{id}`), not the
  inner commons player frame.
- Refresh button: `.xnvc-progress-info-refresh_button.xn-common-white-btn`
  (label "학습 상태 확인").
- Attendance badge: `.xnvc-progress-info-attendance-status`; when attendance is
  granted the modifier token `attendance` is present (blue background, white
  text, label "출석").
- The refresh button can hang forever on a stale session, so waits must be
  bounded and the page reloaded on timeout before retrying.
"""
import asyncio

REFRESH_SELECTOR = '.xnvc-progress-info-refresh_button'
BADGE_SELECTOR = '.xnvc-progress-info-attendance-status'
ATTENDED_TOKENS = frozenset({'attendance', 'attended', 'excused'})
KNOWN_TOKENS = ('attendance', 'attended', 'late', 'absent', 'excused')

READ_JS = """
() => {
  const el = document.querySelector('.xnvc-progress-info-attendance-status');
  return el ? { cls: el.className.toString(), text: (el.innerText||'').trim() } : null;
}
"""

CLICK_JS = """
() => {
  const b = document.querySelector('.xnvc-progress-info-refresh_button');
  if (b) { b.click(); return true; }
  return false;
}
"""


def attendance_token(state: dict | None) -> str | None:
    """Modifier token of the attendance badge (base class is ignored)."""
    if not state:
        return None
    tokens = set((state.get('cls') or '').split())
    return next((token for token in KNOWN_TOKENS if token in tokens), None)


def is_attended(state: dict | None) -> bool:
    return attendance_token(state) in ATTENDED_TOKENS


async def attendance_state(frame) -> dict | None:
    return await frame.evaluate(READ_JS)


async def click_refresh(frame) -> bool:
    return bool(await frame.evaluate(CLICK_JS))


async def verify_attendance(read_state, click_refresh, reload_page, *,
                            timeout: float = 25.0, poll: float = 1.0, reloads: int = 2,
                            sleep=asyncio.sleep) -> dict:
    """Click the status refresh button, bound the wait, reload on timeout.

    ``read_state`` returns the badge ``{cls, text}`` (or None), ``click_refresh``
    presses the button, ``reload_page`` reloads the lecture page. Returns
    ``{'attended': bool, 'attempt': int, 'token': str|None}``.
    """
    attempt = 0
    for attempt in range(1, reloads + 2):
        await click_refresh()
        waited = 0.0
        while waited < timeout:
            state = await read_state()
            if is_attended(state):
                return {'attended': True, 'attempt': attempt, 'token': attendance_token(state)}
            await sleep(poll)
            waited += poll
        if attempt <= reloads:
            await reload_page()
    return {'attended': False, 'attempt': attempt, 'token': None}
