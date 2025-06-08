"""
LMS 강의 다운로드 & 요약 GUI 애플리케이션

메인 진입점 파일
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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

        # Python 경로 설정
        setup_python_path()

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