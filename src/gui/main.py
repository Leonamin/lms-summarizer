"""
LMS 강의 다운로드 & 요약 GUI 애플리케이션

메인 진입점 파일
"""

import sys
import os

def setup_import_path():
    """개발 환경과 PyInstaller 환경 모두에서 동작하도록 import 경로 설정"""
    if getattr(sys, 'frozen', False):
        # PyInstaller로 번들링된 경우
        application_path = sys._MEIPASS
    else:
        # 개발 환경에서 실행되는 경우
        application_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    if application_path not in sys.path:
        sys.path.insert(0, application_path)

# import 경로 설정
setup_import_path()

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QFont

from src.gui.config.constants import APP_TITLE, APP_VERSION
from src.gui.core.module_loader import load_required_modules, setup_python_path
from src.gui.ui.windows.main_window import MainWindow

def setup_application() -> QApplication:
    """QApplication 설정"""
    app = QApplication(sys.argv)
    app.setApplicationName(f"{APP_TITLE} {APP_VERSION}")

    # 폰트 설정
    try:
        font = QFont("맑은 고딕", 10)
        app.setFont(font)
    except:
        pass  # 기본 폰트 사용

    return app


def main():
    """메인 함수"""
    try:
        # QApplication 설정
        app = setup_application()

        # Python 경로 설정 (PyInstaller 환경에서는 무시됨)
        if not getattr(sys, 'frozen', False):
            setup_python_path()

        # 작업 디렉토리 설정
        if getattr(sys, 'frozen', False):
            # PyInstaller 환경에서는 임시 디렉토리를 사용
            os.chdir(sys._MEIPASS)
        else:
            # 개발 환경에서는 스크립트 위치 사용
            os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # 필수 모듈 로드
        modules, errors = load_required_modules()

        # 메인 윈도우 생성 및 실행
        window = MainWindow(modules, errors)
        window.show()

        sys.exit(app.exec_())

    except Exception as e:
        QMessageBox.critical(
            None, "시작 오류",
            f"애플리케이션 시작 중 오류가 발생했습니다:\n{str(e)}\n\n"
            "필요한 모듈들이 설치되어 있는지 확인해주세요."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()