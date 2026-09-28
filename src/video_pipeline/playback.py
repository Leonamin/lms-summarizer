"""Auto-play worker: open a lecture, play to the end, verify attendance (8-B).

Confirmed on the real LMS (2026-09-28, see wiki/logs/2026-09-28-autoplay-dom-investigation.md):
- Play from the inner commons frame via ``.vc-front-screen-play-btn``; an intro
  (``intro.mp4``, ~5s) plays before the real media.
- Resume ("이어서 보시겠습니까") and simultaneous-play ("진도체크 ... 중단됩니다")
  share ``.confirm-msg-box``; the button to proceed is ``.confirm-ok-btn``.
- The status refresh button and attendance badge live in the outer LTI frame
  (see ``src/video_pipeline/attendance.py``).
"""
import asyncio
import json
import time

from src.core.models.jobs import ServiceError, StageResult
from src.core.models.stages import PipelineStage
from src.video_pipeline.attendance import verify_attendance, attendance_state, click_refresh

CONFIRM_BOX = '.confirm-msg-box'
CONFIRM_TEXT = '.confirm-msg-text'
CONFIRM_OK = '.confirm-ok-btn'
FRONT_PLAY = '.vc-front-screen-play-btn'
PLAY_PAUSE = '.vc-pctrl-play-pause-btn'
VIDEO = 'video.vc-vplay-video1, video'

RESUME_HINT = '이어서 보시겠습니까'
SIMULTANEOUS_HINT = '진도체크'


def classify_popup(text: str | None) -> str:
    """Distinguish the shared confirm box: 'resume', 'simultaneous' or 'other'."""
    value = text or ''
    if RESUME_HINT in value or '이어보기' in value:
        return 'resume'
    if SIMULTANEOUS_HINT in value:
        return 'simultaneous'
    return 'other'


async def play_to_end(*, click_play, read_confirm_text, click_confirm, read_progress,
                      click_resume, timeout: float, poll: float = 2.0, popup_limit: int = 3,
                      sleep=asyncio.sleep) -> dict:
    """Play the current lecture to the end while dismissing pop-ups.

    Pop-ups (resume / simultaneous) are confirmed with the positive button. When
    the same attempt sees ``popup_limit`` pop-ups, playback stops and reports
    ``popup_repeat`` so auto-play can pause (ADR-004).
    """
    await click_play()
    elapsed = 0.0
    repeats = 0
    popups: list[str] = []
    while elapsed < timeout:
        text = await read_confirm_text()
        if text:
            repeats += 1
            popups.append(classify_popup(text))
            if repeats >= popup_limit:
                return {'completed': False, 'reason': 'popup_repeat',
                        'popup_repeats': repeats, 'popups': popups}
            await click_confirm()
        state = await read_progress()
        if (state and state.get('dur') and not state.get('intro')
                and state.get('t', 0) >= state['dur'] - 1):
            return {'completed': True, 'popup_repeats': repeats, 'popups': popups, 'state': state}
        if state and state.get('paused'):
            await click_resume()
        await sleep(poll)
        elapsed += poll
    return {'completed': False, 'reason': 'playback_timeout', 'popup_repeats': repeats, 'popups': popups}


# ------------------------------------------------------------------ adapter --
CONFIRM_JS = """
() => {
  const box = document.querySelector('.confirm-msg-box');
  if (!box) return '';
  const r = box.getBoundingClientRect();
  const c = getComputedStyle(box);
  if (!(r.width > 1 && r.height > 1 && c.display !== 'none' && c.visibility !== 'hidden')) return '';
  const t = document.querySelector('.confirm-msg-text');
  return t ? (t.innerText || '').trim() : '';
}
"""

PROGRESS_JS = """
() => {
  const pick = (el) => {
    if (!el) return null;
    const src = el.currentSrc || el.src || '';
    const intro = /intro\\.mp4|preloader\\.mp4/.test(src) || (el.duration && el.duration < 6);
    return { t: el.currentTime, dur: el.duration || 0, paused: el.paused, intro: intro };
  };
  const video = pick(document.querySelector('video.vc-vplay-video1') || document.querySelector('video'));
  const audio = pick(document.querySelector('audio.vc-sdaudio-audio'));
  if (audio && audio.dur && !audio.intro) return audio;
  return video;
}
"""


def _click_js(selector: str) -> str:
    return f"() => {{ const b=document.querySelector({selector!r}); if(b){{ b.click(); return true; }} return false; }}"


async def execute_playback(command) -> StageResult:
    from playwright.async_api import async_playwright
    from src.video_pipeline.login import perform_login_if_needed
    from src.video_pipeline.browser_utils import default_user_agent
    from src.video_pipeline.video_parser import find_canvas_video_frame

    values = json.loads(command.settings_json)
    password = command.credentials.get('lms_password')
    if not password or not values.get('student_id'):
        raise ServiceError('credentials_missing')
    url = command.source
    timeout = float((command.playback or {}).get('play_timeout', 3 * 3600))

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False, executable_path=values.get('chrome_path'),
            args=['--disable-blink-features=AutomationControlled', '--enable-proprietary-codecs',
                  '--no-sandbox', '--autoplay-policy=no-user-gesture-required'])
        context = await browser.new_context(user_agent=default_user_agent())
        page = await context.new_page()
        try:
            await page.goto('https://canvas.ssu.ac.kr/', wait_until='networkidle')
            if 'login' in page.url:
                await perform_login_if_needed(page, values['student_id'], password)
            await page.goto(url, wait_until='networkidle')
            await asyncio.sleep(4)
            try:
                await page.wait_for_selector('iframe#tool_content', timeout=15000)
            except Exception:
                pass
            await asyncio.sleep(3)
            video = await find_canvas_video_frame(page, {})
            if not video:
                return StageResult(command.token, kind='playback',
                                   error_code='playback_failed',
                                   data={'reason': 'no_player'})
            outer = page.frame(name='tool_content')

            async def click_play():
                await video.evaluate(_click_js(FRONT_PLAY))

            async def read_confirm_text():
                return await video.evaluate(CONFIRM_JS)

            async def click_confirm():
                await video.evaluate(_click_js(CONFIRM_OK))

            async def read_progress():
                return await video.evaluate(PROGRESS_JS)

            async def click_resume():
                await video.evaluate(_click_js(PLAY_PAUSE + '.vc-pctrl-on-pause'))
                await video.evaluate(_click_js(FRONT_PLAY))

            result = await play_to_end(click_play=click_play, read_confirm_text=read_confirm_text,
                                       click_confirm=click_confirm, read_progress=read_progress,
                                       click_resume=click_resume, timeout=timeout)
            data = dict(result)
            if not result.get('completed'):
                code = 'popup_repeat' if result.get('reason') == 'popup_repeat' else 'playback_failed'
                return StageResult(command.token, kind='playback', error_code=code, data=data)

            async def reload_page():
                await page.goto(url, wait_until='networkidle')

            attendance = await verify_attendance(
                lambda: attendance_state(outer), lambda: click_refresh(outer), reload_page)
            data['attended'] = attendance['attended']
            if not attendance['attended']:
                return StageResult(command.token, kind='playback', error_code='attendance_pending', data=data)
            return StageResult(command.token, kind='playback', data=data)
        finally:
            await browser.close()
