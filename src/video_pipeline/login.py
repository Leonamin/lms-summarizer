from typing import Callable, Optional

from playwright.sync_api import Page


async def perform_login_if_needed(
    page: Page, username: str, password: str,
    log: Optional[Callable[[str], None]] = None,
) -> bool:
    _log = log or (lambda msg: print(msg))

    _log(f"[LOGIN] 현재 URL: {page.url}")
    if "login" not in page.url:
        return False

    _log("[LOGIN] 로그인 페이지 감지됨. 로그인 시도 중...")

    try:
        login_button = await page.query_selector(".login_btn a")
        if login_button:
            _log("[LOGIN] SSO 로그인 버튼 클릭")
            await login_button.click()
            await page.wait_for_load_state("networkidle")
            _log(f"[LOGIN] SSO 페이지 로드됨. URL: {page.url}")
        else:
            _log("[LOGIN] SSO 로그인 버튼 없음, 직접 폼 입력 시도")

        _log("[LOGIN] 로그인 폼 입력 중...")
        await page.fill("input#userid", username)
        await page.fill("input#pwd", password)

        _log("[LOGIN] 로그인 버튼 클릭")
        async with page.expect_navigation(wait_until="networkidle"):
            await page.click("a.btn_login")

        _log(f"[LOGIN] 리디렉션 완료. URL: {page.url}")

        if "login" in page.url:
            _log("[LOGIN] 로그인 실패. 아이디/비밀번호 확인 필요.")
            return False

        await page.wait_for_load_state("networkidle")
        _log(f"[LOGIN] 최종 페이지 로드 완료. URL: {page.url}")

        return True

    except Exception as e:
        _log(f"[LOGIN] 예외 발생: {type(e).__name__}: {e}")
        return False
