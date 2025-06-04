from playwright.sync_api import Page


async def perform_login_if_needed(page: Page, username: str, password: str) -> bool:
    print(f"[DEBUG] 로그인 체크 전 현재 URL: {page.url}")
    if "login" not in page.url:
        return False

    print("[INFO] 로그인 페이지 감지됨. 로그인 시도 중...")

    try:
        print("[DEBUG] SSO 로그인 버튼 찾는 중...")
        login_button = await page.query_selector(".login_btn a")
        if login_button:
            print("[DEBUG] SSO 로그인 버튼 클릭")
            await login_button.click()
            await page.wait_for_load_state("networkidle")
            print(f"[DEBUG] SSO 페이지 로드됨. 현재 URL: {page.url}")

        print("[DEBUG] 로그인 폼 입력 중...")
        await page.fill("input#userid", username)
        await page.fill("input#pwd", password)

        print("[DEBUG] 로그인 버튼 클릭")
        async with page.expect_navigation(wait_until="networkidle"):
            await page.click("a.btn_login")

        print(f"[DEBUG] 로그인 후 리디렉션 완료. 현재 URL: {page.url}")

        if "login" in page.url:
            print("[ERROR] 로그인 실패. 아이디/비밀번호 확인 필요.")
            return False

        await page.wait_for_load_state("networkidle")
        print(f"[DEBUG] 최종 페이지 로드 완료. 현재 URL: {page.url}")

        return True

    except Exception as e:
        print(f"[ERROR] 로그인 중 예외 발생: {e}")
        return False
