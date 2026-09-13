import asyncio
import re
from pathlib import Path
from playwright.async_api import async_playwright, Playwright, Page
from typing import Callable, Optional, Tuple

from src.video_pipeline.login import perform_login_if_needed, LoginFailedError
from src.video_pipeline.video_parser import extract_video_url
from src.video_pipeline.download_video import download_video
from src.video_pipeline.browser_utils import DEFAULT_CHROME_PATH, default_user_agent
from src.user_setting import UserSetting


def sanitize_dirname(name: str) -> str:
    """디렉토리명에 사용할 수 없는 문자 제거"""
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    sanitized = sanitized.strip(' .')
    sanitized = re.sub(r'\s+', ' ', sanitized)
    return sanitized or 'untitled'


_LOGIN_URL = "https://canvas.ssu.ac.kr/"


class VideoPipeline:
    def __init__(self, user_setting: UserSetting, extraction_timeout: float = 60,
                 progress_callback: Optional[Callable[[int, int], None]] = None,
                 chrome_path: str = None,
                 log_callback: Optional[Callable[[str], None]] = None,
                 headless: bool = False):
        self.user_setting = user_setting
        self.user_id = user_setting.user_id
        self.password = user_setting.password
        self.downloads_dir = None  # 다운로드 경로는 나중에 설정됨
        self.extraction_timeout = extraction_timeout
        self.progress_callback = progress_callback
        self.chrome_path = chrome_path or DEFAULT_CHROME_PATH
        self._log = log_callback or (lambda msg: print(msg))
        self.headless = headless
        self._pw = None
        self._browser = None
        self._session_page = None

    async def _setup_browser(self, playwright: Playwright) -> Tuple[Page, any]:
        """브라우저 설정 및 페이지 생성"""
        browser = await playwright.chromium.launch(
            headless=self.headless,
            executable_path=self.chrome_path,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--enable-proprietary-codecs",
                "--disable-web-security",
                "--auto-open-devtools-for-tabs",
                "--use-fake-ui-for-media-stream",
            ],
        )

        context = await browser.new_context(
            user_agent=default_user_agent(),
            permissions=["camera", "microphone", "geolocation"],
        )

        page = await context.new_page()
        await page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            window.chrome = { runtime: {} };
            """
        )

        return page, browser

    async def _ensure_logged_in(self, page: Page):
        """대시보드로 이동하여 로그인 선행 처리 (CourseScraper 패턴)"""
        self._log("LMS 로그인 확인 중...")
        await page.goto(_LOGIN_URL, wait_until="networkidle")

        if "login" in page.url:
            self._log("로그인 진행 중...")
            await perform_login_if_needed(
                page, self.user_id, self.password, log=self._log
            )
            self._log("로그인 완료")
        else:
            self._log("이미 로그인 상태")

    async def _process_single_url(self, page: Page, url: str) -> Optional[str]:
        """단일 URL에 대한 비디오 처리"""
        self._log(f"처리 중: {url}")
        await page.goto(url, wait_until="networkidle")
        self._log(f"페이지 이동 완료: {page.url}")

        video_url, title = await extract_video_url(page, method="cdp", timeout=self.extraction_timeout, log=self._log)

        if video_url:
            self._log(f"동영상 링크 추출됨: {video_url}")

            # 강의 이름으로 하위 디렉토리 생성
            save_dir = self.downloads_dir
            if title and save_dir:
                lecture_dir = Path(save_dir) / sanitize_dirname(title)
                lecture_dir.mkdir(parents=True, exist_ok=True)
                save_dir = str(lecture_dir)

            filepath = download_video(video_url, save_dir=save_dir, filename=title,
                                     progress_callback=self.progress_callback)
            self._log(f"동영상 다운로드 완료: {filepath}")
            return filepath
        else:
            self._log("[WARN] 동영상 링크를 찾지 못했습니다.")
            return None

    async def open_session(self):
        """브라우저 세션 열기 (로그인까지 수행, 이후 process_single_url로 재사용)"""
        self._pw = await async_playwright().start()
        self._log(f"Playwright 시작, Chrome: {self.chrome_path}")
        page, browser = await self._setup_browser(self._pw)
        self._browser = browser
        self._session_page = page
        self._log("브라우저 시작 완료")
        await self._ensure_logged_in(page)

    async def close_session(self):
        """브라우저 세션 닫기"""
        try:
            if self._browser:
                await self._browser.close()
        finally:
            self._browser = None
            self._session_page = None
            if self._pw:
                try:
                    await self._pw.stop()
                except Exception:
                    pass
                self._pw = None

    async def process_single_url(self, url: str) -> Optional[str]:
        """열린 세션에서 단일 URL 처리 (다운로드 완료 파일 경로 또는 None)"""
        if not self._session_page:
            raise RuntimeError("브라우저 세션이 없습니다. open_session()을 먼저 호출하세요.")
        return await self._process_single_url(self._session_page, url)

    async def process(self, urls: list[str]) -> list[str]:
        """비디오 다운로드 파이프라인 실행"""
        downloaded_videos_path = []
        failed_urls = []

        await self.open_session()
        try:
            for i, url in enumerate(urls, 1):
                try:
                    filepath = await self.process_single_url(url)
                    if filepath:
                        downloaded_videos_path.append(filepath)
                except Exception as e:
                    self._log(f"[ERROR] ({i}/{len(urls)}) 다운로드 실패, 다음 영상으로 진행: {url}")
                    self._log(f"[ERROR] 원인: {type(e).__name__}: {e}")
                    failed_urls.append((url, str(e)))
        finally:
            await self.close_session()

        if failed_urls:
            self._log(f"[WARN] {len(failed_urls)}개 영상 다운로드 실패:")
            for url, err in failed_urls:
                self._log(f"  - {url}: {err}")

        return downloaded_videos_path

    def process_sync(self, urls: list[str]) -> list[str]:
        """동기 방식으로 파이프라인 실행"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.process(urls))
        finally:
            loop.close()
