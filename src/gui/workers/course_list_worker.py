"""
과목/강의 목록을 백그라운드에서 로드하는 워커 스레드
"""

import asyncio
import threading
import traceback
from typing import Optional, Callable, List

from src.gui.config.course_models import Course
from src.gui.core.file_manager import get_chrome_path, get_debug_mode
from src.video_pipeline.login import LoginFailedError


class CourseListWorker:
    """과목 또는 강의 목록을 로드하는 워커"""

    def __init__(
        self,
        username: str,
        password: str,
        course: Optional[Course] = None,
        on_log: Optional[Callable[[str], None]] = None,
        on_courses_loaded: Optional[Callable[[List], None]] = None,
        on_lectures_loaded: Optional[Callable] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_finished: Optional[Callable[[], None]] = None,
    ):
        """
        course=None: 과목 목록 로드
        course 지정: 해당 과목의 강의 목록 로드
        """
        self.username = username
        self.password = password
        self.course = course
        self.chrome_path = get_chrome_path()
        self.debug_mode = get_debug_mode()
        self._cancel_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # 콜백
        self._on_log = on_log or (lambda msg: None)
        self._on_courses_loaded = on_courses_loaded or (lambda courses: None)
        self._on_lectures_loaded = on_lectures_loaded or (lambda detail: None)
        self._on_error = on_error or (lambda msg: None)
        self._on_finished = on_finished or (lambda: None)

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def request_cancel(self):
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def join(self, timeout: float = None):
        if self._thread:
            self._thread.join(timeout=timeout)

    def _run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_run())
        except LoginFailedError as e:
            if not self._cancel_event.is_set():
                self._on_error(f"로그인 실패: {e.detail}")
        except Exception as e:
            if not self._cancel_event.is_set():
                self._on_error(str(e))
                self._on_log(f"[ERROR] {traceback.format_exc()}")
        finally:
            self._on_finished()

    async def _async_run(self):
        from src.video_pipeline.course_scraper import CourseScraper

        def log_cb(msg):
            self._on_log(msg)

        async with CourseScraper(
            self.username, self.password,
            chrome_path=self.chrome_path,
            headless=not self.debug_mode,
            log_callback=log_cb,
        ) as scraper:
            if self._cancel_event.is_set():
                return

            if self.course is None:
                courses = await scraper.fetch_courses()
                if not self._cancel_event.is_set():
                    self._on_courses_loaded(courses)
            else:
                detail = await scraper.fetch_lectures(self.course)
                if not self._cancel_event.is_set():
                    self._on_lectures_loaded(detail)
