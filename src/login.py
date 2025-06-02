from playwright.sync_api import Page
import time

def perform_login_if_needed(page: Page, username: str, password: str) -> bool:
    # 이미 로그인된 상태인지 확인
    if "login" not in page.url:
        return False  # 로그인 불필요

    print("[INFO] 로그인 페이지 감지됨. 로그인 시도 중...")

    try:
        # 1. 로그인 버튼 클릭
        login_button = page.query_selector(".login_btn a")
        if login_button:
            login_button.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)

        # 2. 아이디/비밀번호 입력
        page.fill("input#userid", username)
        page.fill("input#pwd", password)

        # 3. 로그인 버튼 클릭
        page.click("a.btn_login")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # 4. 로그인 성공 여부 확인 (다시 로그인 페이지면 실패)
        if "login" in page.url:
            print("[ERROR] 로그인 실패. 아이디/비밀번호 확인 필요.")
            return False

        return True

    except Exception as e:
        print(f"[ERROR] 로그인 중 예외 발생: {e}")
        return False
