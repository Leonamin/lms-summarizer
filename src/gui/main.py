"""
LMS Summarizer GUI 엔트리포인트 (Flet)
"""

import os
import sys


def setup_import_path():
    """개발 환경과 PyInstaller 환경 모두에서 동작하도록 import 경로 설정"""
    if getattr(sys, 'frozen', False):
        application_path = sys._MEIPASS
    else:
        application_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    if application_path not in sys.path:
        sys.path.insert(0, application_path)


# import 경로 설정
setup_import_path()


def main():
    """메인 함수"""
    import flet as ft
    from src.gui.theme import setup_page_theme
    from src.gui.core.module_loader import load_required_modules
    from src.gui.views.main_view import MainView

    def app_main(page: ft.Page):
        setup_page_theme(page)

        # 백엔드 모듈 로드
        modules, errors = load_required_modules()

        # 메인 뷰 생성
        MainView(page, modules, errors)

    ft.app(target=app_main)


if __name__ == "__main__":
    main()
