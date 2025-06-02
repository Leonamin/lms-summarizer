from playwright.sync_api import Page
import time

def perform_login_if_needed(page: Page, username: str, password: str) -> bool:
    # 이미 로그인된 상태인지 확인
    print(f"[DEBUG] 로그인 체크 전 현재 URL: {page.url}")
    if "login" not in page.url:
        return False  # 로그인 불필요

    print("[INFO] 로그인 페이지 감지됨. 로그인 시도 중...")

    try:
        # 1. 로그인 버튼 클릭
        print("[DEBUG] SSO 로그인 버튼 찾는 중...")
        login_button = page.query_selector(".login_btn a")
        if login_button:
            print("[DEBUG] SSO 로그인 버튼 클릭")
            login_button.click()
            page.wait_for_load_state("networkidle")
            print(f"[DEBUG] SSO 페이지 로드됨. 현재 URL: {page.url}")

        # 2. 아이디/비밀번호 입력
        print("[DEBUG] 로그인 폼 입력 중...")
        page.fill("input#userid", username)
        page.fill("input#pwd", password)

        # 3. 로그인 버튼 클릭 및 리디렉션 대기
        print("[DEBUG] 로그인 버튼 클릭")
        
        # Promise.all을 사용하여 네비게이션과 클릭을 동시에 처리
        with page.expect_navigation(wait_until="networkidle"):
            page.click("a.btn_login")
        
        print(f"[DEBUG] 로그인 후 리디렉션 완료. 현재 URL: {page.url}")

        # 4. 로그인 성공 여부 확인 (다시 로그인 페이지면 실패)
        if "login" in page.url:
            print("[ERROR] 로그인 실패. 아이디/비밀번호 확인 필요.")
            return False

        # 추가 리디렉션 대기
        page.wait_for_load_state("networkidle")
        print(f"[DEBUG] 최종 페이지 로드 완료. 현재 URL: {page.url}")
        
        return True

    except Exception as e:
        print(f"[ERROR] 로그인 중 예외 발생: {e}")
        return False
