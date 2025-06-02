from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # headless=False로 하면 브라우저 뜸
    context = browser.new_context()
    page = context.new_page()

    # 요청 추적 콜백
    def handle_request(request):
        if "ssmovie.mp4" in request.url:
            print("찾은 요청 URL:", request.url)

    page.on("request", handle_request)

    # 접속 및 인터랙션
    page.goto("https://canvas.ssu.ac.kr/courses/35549/modules/items/3158488")
    page.click(".vc-front-screen-play-btn")
    page.wait_for_timeout(8000)

    browser.close()
