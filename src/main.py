import time
from playwright.sync_api import sync_playwright, Playwright, Page

from config import load_config, config
from login import perform_login_if_needed
from video_parser import download_video, extract_video_url


def get_video_urls() -> list[str]:
    print("다운로드할 링크를 입력하세요. 0 또는 빈 줄을 입력하면 종료됩니다.")
    urls = []
    while True:
        url = input("링크: ")
        if url == "0" or url == "":
            break
        error = validate_url(url)
        if error:
            print(error)
            continue
        urls.append(url)
    return urls


def validate_url(url: str) -> str:
    # return type: 빈문자열인 경우 통과
    # 아닌 경우 오류 메시지 반환
    if not url.startswith("https://canvas.ssu.ac.kr/courses/"):
        return "올바른 링크가 아닙니다. 다시 입력해주세요."
    return ""


def open_as_firefox(p: Playwright) -> tuple[Page, any]:
    # 파이어폭스는 동영상 컨텐츠 재생에 성공하지만 깊은 네트워크 감지가 안됨
    browser = p.firefox.launch(headless=False)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
        java_script_enabled=True,
        has_touch=False,
        is_mobile=False,
    )

    page = context.new_page()

    page.add_init_script(
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


def open_as_chrome(p: Playwright) -> tuple[Page, any]:
    # 크롬은 개발자 콘솔 사용이 가능하지만 동영상 컨텐츠 재생에 실패함
    browser = p.chromium.launch(
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
    context = browser.new_context(
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

    page = context.new_page()
    page.add_init_script(
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

def open_as_chrome_installed(p: Playwright) -> tuple[Page, any]:
    browser = p.chromium.launch(
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

    context = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        permissions=["camera", "microphone", "geolocation"],
    )

    page = context.new_page()
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        window.chrome = { runtime: {} };
    """)

    return page, browser


open_webbrowser = {
    'F': open_as_firefox,
    'C': open_as_chrome,
    'CI': open_as_chrome_installed,
}

def main():
    load_config()
    urls = get_video_urls()
    print(urls)

    with sync_playwright() as p:
        page, browser = open_webbrowser['CI'](p)

        try:
            for url in urls:
                print(f"\n[INFO] 처리 중: {url}")
                # 페이지 이동 및 로딩 대기
                page.goto(url, wait_until="networkidle")
                print(f"[DEBUG] 페이지 이동 완료: {page.url}")

                # 로그인 필요 여부 판단 및 처리
                if perform_login_if_needed(page, config["USERID"], config["PASSWORD"]):
                    print("[INFO] 로그인 완료 또는 유지됨.")
                    # 로그인 후 페이지 로딩 대기
                    page.wait_for_load_state("networkidle")
                    print(f"[DEBUG] 로그인 후 현재 URL: {page.url}")
                else:
                    print("[INFO] 로그인 불필요.")

                # 동영상 URL 추출 시도
                video_url = extract_video_url(page)

                if video_url:
                    print(f"[SUCCESS] 동영상 링크 추출됨: {video_url}")
                    download_video(video_url)
                else:
                    print("[WARN] 동영상 링크를 찾지 못했습니다.")

            time.sleep(1000000)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
