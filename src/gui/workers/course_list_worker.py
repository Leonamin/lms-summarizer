"""
과목/강의 목록을 백그라운드에서 로드하는 워커 스레드
"""

import asyncio
import threading
import traceback
from typing import Optional

from PyQt5.QtCore import QThread, pyqtSignal

from src.gui.config.course_models import Course
from src.gui.core.file_manager import get_chrome_path


class CourseListWorker(QThread):
    """과목 또는 강의 목록을 로드하는 워커"""

    log_message = pyqtSignal(str)
    courses_loaded = pyqtSignal(list)       # List[Course]
    lectures_loaded = pyqtSignal(object)    # CourseDetail
    error_occurred = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, username: str, password: str,
                 course: Optional[Course] = None):
        """
        course=None: 과목 목록 로드
        course 지정: 해당 과목의 강의 목록 로드
        """
        super().__init__()
        self.username = username
        self.password = password
        self.course = course
        self.chrome_path = get_chrome_path()
        self._cancel_event = threading.Event()

    def request_cancel(self):
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_run())
        except Exception as e:
            if not self._cancel_event.is_set():
                self.error_occurred.emit(str(e))
                self.log_message.emit(f"[ERROR] {traceback.format_exc()}")
        finally:
            self.finished_signal.emit()

    async def _async_run(self):
        from src.video_pipeline.course_scraper import CourseScraper

        def log_cb(msg):
            self.log_message.emit(msg)

        async with CourseScraper(
            self.username, self.password,
            chrome_path=self.chrome_path,
            log_callback=log_cb,
        ) as scraper:
            if self._cancel_event.is_set():
                return

            if self.course is None:
                courses = await scraper.fetch_courses()
                if not self._cancel_event.is_set():
                    self.courses_loaded.emit(courses)
            else:
                detail = await scraper.fetch_lectures(self.course)
                if not self._cancel_event.is_set():
                    self.lectures_loaded.emit(detail)
