import asyncio
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright, Playwright, Page

from login import perform_login_if_needed
from video_parser import download_video, extract_video_url
from user_setting import UserSetting


def get_video_urls(user_setting: UserSetting) -> list[str]:
    result = user_setting.get_video_urls()
    if result:
        return result
    return user_setting.input_video_urls()


async def open_as_firefox(p: Playwright) -> tuple[Page, any]:
    # 파이어폭스는 동영상 컨텐츠 재생에 성공하지만 깊은 네트워크 감지가 안됨
    browser = await p.firefox.launch(headless=False)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
        java_script_enabled=True,
        has_touch=False,
        is_mobile=False,
    )

    page = await context.new_page()

    await page.add_init_script(
        """
        // Firefox-specific 자동화 감지 방지
        Object.defineProperty(window.navigator, 'webdriver', {
            get: () => false,
            configurable: true
        });

        // Firefox의 자동화 관련 속성 수정
        Object.defineProperty(navigator, 'platform', {
            get: () => 'MacIntel'
        });
        """
    )
    return page, browser


async def open_as_chrome(p: Playwright) -> tuple[Page, any]:
    # 크롬은 개발자 콘솔 사용이 가능하지만 동영상 컨텐츠 재생에 실패함
    browser = await p.chromium.launch(
        headless=False,
        args=[
            "--autoplay-policy=no-user-gesture-required",
            "--enable-automation",
            "--enable-features=NetworkService,NetworkServiceInProcess",
            "--allow-running-insecure-content",
            "--disable-site-isolation-trials",
            "--disable-blink-features=AutomationControlled"
            "--enable-usermedia-screen-capturing",
            "--use-fake-ui-for-media-stream",
            "--disable-web-security",
            "--enable-proprietary-codecs",
        ],
    )
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Whale/4.31.304.16 Safari/537.36",
        java_script_enabled=True,
        has_touch=False,
        is_mobile=False,
        # 추가 권한 설정
        permissions=["camera", "microphone", "geolocation"],
    )

    # 추가 브라우저 설정
    context.set_extra_http_headers(
        {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
    )

    page = await context.new_page()
    await page.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        window.chrome = {
            runtime: {}
        };
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) =>
            parameters.name === "notifications"
                ? Promise.resolve({ state: "denied" })
                : originalQuery(parameters);
        """
    )
    return page, browser


async def open_as_chrome_installed(p: Playwright) -> tuple[Page, any]:
    browser = await p.chromium.launch(
        headless=False,
        executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS 기준
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


open_webbrowser = {
    "F": open_as_firefox,
    "C": open_as_chrome,
    "CI": open_as_chrome_installed,
}


async def async_main():
    user_setting = UserSetting()
    user_id, password = user_setting.get_user_account()
    print(f"[INFO] 사용자 계정: {user_id}, 비밀번호 유무: {password is not None}")
    if not user_id or not password:
        print("[ERROR] 사용자 계정 또는 비밀번호가 설정되지 않았습니다.")
        return

    urls = get_video_urls(user_setting)
    print(f"[INFO] 다운로드할 링크: {len(urls)}개")

    async with async_playwright() as p:
        page, browser = await open_webbrowser["CI"](p)

        try:
            for url in urls:
                print(f"\n[INFO] 처리 중: {url}")
                await page.goto(url, wait_until="networkidle")
                print(f"[DEBUG] 페이지 이동 완료: {page.url}")

                if await perform_login_if_needed(page, user_id, password):
                    print("[INFO] 로그인 완료 또는 유지됨.")
                    await page.wait_for_load_state("networkidle")
                    print(f"[DEBUG] 로그인 후 현재 URL: {page.url}")
                else:
                    print("[INFO] 로그인 불필요.")

                video_url = await extract_video_url(page)

                if video_url:
                    print(f"[SUCCESS] 동영상 링크 추출됨: {video_url}")
                    download_video(video_url)
                else:
                    print("[WARN] 동영상 링크를 찾지 못했습니다.")

        finally:
            await browser.close()

# 진입점
if __name__ == "__main__":
    asyncio.run(async_main())
