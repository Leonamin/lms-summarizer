import asyncio
import re
from pathlib import Path
from playwright.async_api import async_playwright, Playwright, Page
from typing import Callable, Optional, Tuple

from src.video_pipeline.login import perform_login_if_needed
from src.video_pipeline.video_parser import extract_video_url
from src.video_pipeline.download_video import download_video
from src.user_setting import UserSetting


def sanitize_dirname(name: str) -> str:
    """디렉토리명에 사용할 수 없는 문자 제거"""
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    sanitized = sanitized.strip(' .')
    sanitized = re.sub(r'\s+', ' ', sanitized)
    return sanitized or 'untitled'


class VideoPipeline:
    def __init__(self, user_setting: UserSetting, extraction_timeout: float = 60,
                 progress_callback: Optional[Callable[[int, int], None]] = None):
        self.user_setting = user_setting
        self.user_id = user_setting.user_id
        self.password = user_setting.password
        self.downloads_dir = None  # 다운로드 경로는 나중에 설정됨
        self.extraction_timeout = extraction_timeout
        self.progress_callback = progress_callback

    async def _setup_browser(self, playwright: Playwright) -> Tuple[Page, any]:
        """브라우저 설정 및 페이지 생성"""
        browser = await playwright.chromium.launch(
            headless=False,
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--enable-proprietary-codecs",
                "--disable-web-security",
                "--auto-open-devtools-for-tabs",
                "--use-fake-ui-for-media-stream",
            ],
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
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

    async def _process_single_url(self, page: Page, url: str) -> Optional[str]:
        """단일 URL에 대한 비디오 처리"""
        print(f"\n[INFO] 처리 중: {url}")
        await page.goto(url, wait_until="networkidle")
        print(f"[DEBUG] 페이지 이동 완료: {page.url}")

        if await perform_login_if_needed(page, self.user_id, self.password):
            print("[INFO] 로그인 완료 또는 유지됨.")
            await page.wait_for_load_state("networkidle")
            print(f"[DEBUG] 로그인 후 현재 URL: {page.url}")
        else:
            print("[INFO] 로그인 불필요.")

        video_url, title = await extract_video_url(page, method="dom", timeout=self.extraction_timeout)

        if video_url:
            print(f"[SUCCESS] 동영상 링크 추출됨: {video_url}, 제목: {title}")

            # 강의 이름으로 하위 디렉토리 생성
            save_dir = self.downloads_dir
            if title and save_dir:
                lecture_dir = Path(save_dir) / sanitize_dirname(title)
                lecture_dir.mkdir(parents=True, exist_ok=True)
                save_dir = str(lecture_dir)
                print(f"[INFO] 강의 폴더: {save_dir}")

            filepath = download_video(video_url, save_dir=save_dir, filename=title,
                                     progress_callback=self.progress_callback)
            print(f"[SUCCESS] 동영상 다운로드 완료: {filepath}")
            return filepath
        else:
            print("[WARN] 동영상 링크를 찾지 못했습니다.")
            return None

    async def process(self, urls: list[str]) -> list[str]:
        """비디오 다운로드 파이프라인 실행"""
        downloaded_videos_path = []

        async with async_playwright() as p:
            page, browser = await self._setup_browser(p)

            try:
                for url in urls:
                    filepath = await self._process_single_url(page, url)
                    if filepath:
                        downloaded_videos_path.append(filepath)
            finally:
                await browser.close()

        return downloaded_videos_path

    def process_sync(self, urls: list[str]) -> list[str]:
        """동기 방식으로 파이프라인 실행"""
        return asyncio.run(self.process(urls))
