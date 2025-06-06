"""
LMS 강의 다운로드 & 요약 GUI 애플리케이션

이 애플리케이션은 숭실대학교 LMS에서 강의 동영상을 다운로드하고
AI를 사용하여 자동으로 요약하는 기능을 제공합니다.
"""

import sys
import os
import json
import traceback
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# =============================================================================
# 설정 및 상수
# =============================================================================

APP_TITLE = "LMS 강의 다운로드 & 요약"
APP_VERSION = "v1.0"
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 800


@dataclass
class Colors:
    """앱에서 사용하는 색상 정의"""
    PRIMARY = "#3498db"
    PRIMARY_HOVER = "#2980b9"
    PRIMARY_PRESSED = "#1f648f"
    BACKGROUND = "#ecf0f1"
    TEXT_DARK = "#2c3e50"
    TEXT_SECONDARY = "#34495e"
    TEXT_LIGHT = "#7f8c8d"
    LOG_BG = "#2c3e50"
    LOG_TEXT = "#ecf0f1"
    SUCCESS = "#27ae60"
    WARNING = "#f39c12"
    ERROR = "#e74c3c"


@dataclass
class InputFieldConfig:
    """입력 필드 설정"""
    label: str
    placeholder: str
    is_password: bool = False
    is_multiline: bool = False
    max_height: Optional[int] = None


# =============================================================================
# 유틸리티 함수
# =============================================================================

def get_resource_path(relative_path: str) -> str:
    """PyInstaller 환경에서도 작동하는 리소스 경로 반환"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def setup_python_path():
    """Python 경로 설정"""
    app_path = os.path.dirname(__file__) if not getattr(sys, 'frozen', False) else sys._MEIPASS
    src_path = os.path.join(app_path, 'src')

    for path in [src_path, app_path]:
        if path not in sys.path:
            sys.path.insert(0, path)

    return app_path, src_path


def load_required_modules():
    """필수 모듈들을 로드하고 결과 반환"""
    modules = {}
    errors = []

    module_imports = {
        'UserSetting': 'user_setting.UserSetting',
        'VideoPipeline': 'video_pipeline.pipeline.VideoPipeline',
        'AudioToTextPipeline': 'audio_pipeline.pipeline.AudioToTextPipeline',
        'SummarizePipeline': 'summarize_pipeline.pipeline.SummarizePipeline'
    }

    for name, import_path in module_imports.items():
        try:
            module_parts = import_path.split('.')
            module = __import__('.'.join(module_parts[:-1]), fromlist=[module_parts[-1]])
            modules[name] = getattr(module, module_parts[-1])
            print(f"[SUCCESS] {name} 모듈 로드 완료")
        except ImportError as e:
            modules[name] = None
            errors.append(f"{name}: {e}")
            print(f"[ERROR] {name} 로드 실패: {e}")

    return modules, errors


# =============================================================================
# 스타일 관리
# =============================================================================

class StyleSheet:
    """UI 스타일시트 관리 클래스"""

    @staticmethod
    def title() -> str:
        return f"""
            font-size: 24px;
            font-weight: bold;
            margin: 20px;
            color: {Colors.TEXT_DARK};
        """

    @staticmethod
    def label() -> str:
        return f"""
            margin-top: 10px; 
            margin-bottom: 5px; 
            font-weight: bold;
            color: {Colors.TEXT_SECONDARY};
            font-size: 14px;
        """

    @staticmethod
    def input_field() -> str:
        return f"""
            padding: 12px;
            font-size: 14px;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin-bottom: 10px;
            background-color: white;
        """

    @staticmethod
    def multiline_input() -> str:
        return f"""
            {StyleSheet.input_field()}
            min-width: 500px;
            min-height: 100px;
        """

    @staticmethod
    def button() -> str:
        return f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                margin-top: 20px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_PRESSED};
            }}
            QPushButton:disabled {{
                background-color: #bdc3c7;
                color: {Colors.TEXT_LIGHT};
            }}
        """

    @staticmethod
    def log_area() -> str:
        return f"""
            background-color: {Colors.LOG_BG};
            color: {Colors.LOG_TEXT};
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #34495e;
        """


# =============================================================================
# 워커 스레드
# =============================================================================

class ProcessingWorker(QThread):
    """백그라운드에서 LMS 처리 작업을 수행하는 워커 스레드"""

    # 시그널 정의
    log_message = pyqtSignal(str)
    processing_finished = pyqtSignal(bool, str)

    def __init__(self, user_inputs: Dict[str, str], modules: Dict):
        super().__init__()
        self.user_inputs = user_inputs
        self.modules = modules

    def run(self):
        """실제 처리 작업 실행"""
        try:
            self._emit_log("🚀 LMS 요약 작업을 시작합니다...")

            if not self._validate_modules():
                return

            self._create_config_files()
            self._process_videos()
            self._emit_log("🎉 모든 작업이 완료되었습니다!")

            self.processing_finished.emit(True, "작업이 성공적으로 완료되었습니다.")

        except Exception as e:
            error_msg = f"작업 중 오류 발생: {str(e)}"
            self._emit_log(f"❌ {error_msg}")
            self._emit_log(f"상세 오류:\n{traceback.format_exc()}")
            self.processing_finished.emit(False, error_msg)

    def _emit_log(self, message: str):
        """로그 메시지 출력"""
        self.log_message.emit(message)

    def _validate_modules(self) -> bool:
        """필수 모듈 확인"""
        missing = [name for name, module in self.modules.items() if module is None]
        if missing:
            self._emit_log(f"❌ 필수 모듈 누락: {', '.join(missing)}")
            self._emit_log("pip install -r requirements.txt 실행 후 재시작하세요.")
            self.processing_finished.emit(False, f"필수 모듈 누락: {', '.join(missing)}")
            return False
        return True

    def _create_config_files(self):
        """설정 파일들 생성"""
        self._emit_log("📝 설정 파일 생성 중...")

        # .env 파일 생성
        env_content = f"""USERID={self.user_inputs.get('student_id', '')}
PASSWORD={self.user_inputs.get('password', '')}
GOOGLE_API_KEY={self.user_inputs.get('api_key', '')}
"""
        with open(get_resource_path('.env'), 'w', encoding='utf-8') as f:
            f.write(env_content)

        # user_settings.json 파일 생성
        urls = self._extract_urls()
        settings = {"video": urls}
        with open(get_resource_path('user_settings.json'), 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)

    def _extract_urls(self) -> List[str]:
        """입력에서 URL 목록 추출"""
        url_text = self.user_inputs.get('urls', '').strip()
        return [url.strip() for url in url_text.split('\n') if url.strip()] if url_text else []

    def _process_videos(self):
        """비디오 처리 파이프라인 실행"""
        user_setting = self.modules['UserSetting']()
        urls = self._extract_urls()

        # 1. 비디오 다운로드
        self._emit_log(f"📹 {len(urls)}개 비디오 다운로드 시작...")
        video_pipeline = self.modules['VideoPipeline'](user_setting)
        video_paths = video_pipeline.process_sync(urls)
        self._emit_log(f"✅ {len(video_paths)}개 비디오 다운로드 완료")

        # 2. 음성을 텍스트로 변환
        self._emit_log("🎵 음성을 텍스트로 변환 중...")
        audio_pipeline = self.modules['AudioToTextPipeline']()
        text_paths = []

        for i, video_path in enumerate(video_paths, 1):
            try:
                self._emit_log(f"🎤 ({i}/{len(video_paths)}) 변환 중: {Path(video_path).name}")
                text_path = audio_pipeline.process(video_path)
                text_paths.append(text_path)
                self._emit_log(f"✅ 변환 완료: {text_path}")
            except Exception as e:
                self._emit_log(f"❌ 변환 실패 ({Path(video_path).name}): {e}")

        # 3. 텍스트 요약
        self._emit_log("🤖 AI 요약 생성 중...")
        summarize_pipeline = self.modules['SummarizePipeline']()

        for i, text_path in enumerate(text_paths, 1):
            try:
                self._emit_log(f"📝 ({i}/{len(text_paths)}) 요약 중: {Path(text_path).name}")
                summary_path = summarize_pipeline.process(text_path)
                self._emit_log(f"✅ 요약 완료: {summary_path}")
            except Exception as e:
                self._emit_log(f"❌ 요약 실패 ({Path(text_path).name}): {e}")


# # =============================================================================
# # UI 컴포넌트
# # =============================================================================
#
# class InputField:
#     """입력 필드를 관리하는 클래스"""
#
#     def __init__(self, config: InputFieldConfig):
#         self.config = config
#         self.label = self._create_label()
#         self.widget = self._create_input_widget()
#
#     def _create_label(self) -> QLabel:
#         label = QLabel(self.config.label)
#         label.setStyleSheet(StyleSheet.label())
#         return label
#
#     def _create_input_widget(self):
#         if self.config.is_multiline:
#             widget = QTextEdit()
#             widget.setPlaceholderText(self.config.placeholder)
#             widget.setStyleSheet(StyleSheet.multiline_input())
#             if self.config.max_height:
#                 widget.setMaximumHeight(self.config.max_height)
#         else:
#             widget = QLineEdit()
#             widget.setPlaceholderText(self.config.placeholder)
#             widget.setStyleSheet(StyleSheet.input_field())
#             if self.config.is_password:
#                 widget.setEchoMode(QLineEdit.Password)
#
#         return widget
#
#     def get_value(self) -> str:
#         """입력값 반환"""
#         if hasattr(self.widget, 'toPlainText'):
#             return self.widget.toPlainText()
#         return self.widget.text()


class MainWindow(QWidget):
    """메인 윈도우 클래스"""

    def __init__(self, modules: Dict, module_errors: List[str]):
        super().__init__()
        self.modules = modules
        self.module_errors = module_errors
        self.input_fields = {}
        self.log_area = None
        self.start_button = None
        self.worker = None

        self._setup_window()
        self._setup_ui()
        self._check_module_status()

    def _setup_window(self):
        """윈도우 기본 설정"""
        self.setWindowTitle(f"{APP_TITLE} {APP_VERSION}")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setStyleSheet(f"background-color: {Colors.BACKGROUND};")

    def _setup_ui(self):
        """UI 구성요소 설정"""
        layout = QVBoxLayout()

        # 제목
        title = QLabel(f"🎓 {APP_TITLE}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(StyleSheet.title())
        layout.addWidget(title)

        # 설명
        description = QLabel("📖 숭실대학교 LMS 강의 동영상을 다운로드하고 AI로 요약합니다.")
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet(f"color: {Colors.TEXT_LIGHT}; font-size: 12px; margin-bottom: 20px;")
        layout.addWidget(description)

        # 입력 필드들
        self._create_input_fields(layout)

        # 버튼
        self._create_buttons(layout)

        # 로그 영역
        self._create_log_area(layout)

        self.setLayout(layout)

    def _create_input_fields(self, layout: QVBoxLayout):
        """입력 필드들 생성"""
        field_configs = {
            'student_id': InputFieldConfig("📚 학번:", "예: 20201234"),
            'password': InputFieldConfig("🔒 비밀번호:", "LMS 비밀번호", is_password=True),
            'api_key': InputFieldConfig("🔑 Gemini API 키:", "sk-... (Gemini API 키를 입력하세요)"),
            'urls': InputFieldConfig(
                "🎬 강의 URL 목록:",
                "https://canvas.ssu.ac.kr/courses/...\n(여러 URL은 각각 새 줄에 입력)",
                is_multiline=True,
                max_height=120
            )
        }

        for name, config in field_configs.items():
            field = InputField(config)
            self.input_fields[name] = field
            layout.addWidget(field.label)
            layout.addWidget(field.widget)

    def _create_buttons(self, layout: QVBoxLayout):
        """버튼들 생성"""
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("🚀 요약 시작")
        self.start_button.setStyleSheet(StyleSheet.button())
        self.start_button.clicked.connect(self._start_processing)

        button_layout.addWidget(self.start_button)
        layout.addLayout(button_layout)

    def _create_log_area(self, layout: QVBoxLayout):
        """로그 영역 생성"""
        log_label = QLabel("📋 작업 로그:")
        log_label.setStyleSheet(StyleSheet.label())
        layout.addWidget(log_label)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet(StyleSheet.log_area())
        self.log_area.setMaximumHeight(300)
        self.log_area.setPlainText("📋 작업 로그가 여기에 표시됩니다...\n")
        layout.addWidget(self.log_area)

    def _check_module_status(self):
        """모듈 상태 확인 및 경고 표시"""
        if self.module_errors:
            self._append_log("⚠️ 일부 모듈 로드 실패:")
            for error in self.module_errors:
                self._append_log(f"   - {error}")
            self._append_log("pip install -r requirements.txt 실행 후 재시작하세요.")

    def _validate_inputs(self) -> bool:
        """입력값 유효성 검사"""
        validations = [
            ('student_id', '학번을 입력해주세요.'),
            ('password', '비밀번호를 입력해주세요.'),
            ('api_key', 'Gemini API 키를 입력해주세요.'),
            ('urls', '강의 URL을 입력해주세요.')
        ]

        for field_name, error_msg in validations:
            if not self.input_fields[field_name].get_value().strip():
                QMessageBox.warning(self, "입력 오류", error_msg)
                return False

        return True

    def _start_processing(self):
        """처리 시작"""
        if not self._validate_inputs():
            return

        # 필수 모듈 확인
        missing_modules = [name for name, module in self.modules.items() if module is None]
        if missing_modules:
            QMessageBox.critical(
                self, "모듈 오류",
                f"❌ 필수 모듈들이 로드되지 않았습니다: {', '.join(missing_modules)}\n\n"
                "pip install -r requirements.txt 실행 후 재시작하세요."
            )
            return

        # 입력값 수집
        inputs = {name: field.get_value() for name, field in self.input_fields.items()}

        # UI 상태 변경
        self.start_button.setEnabled(False)
        self.start_button.setText("⏳ 처리 중...")
        self.log_area.clear()

        # 워커 스레드 시작
        self.worker = ProcessingWorker(inputs, self.modules)
        self.worker.log_message.connect(self._append_log)
        self.worker.processing_finished.connect(self._on_processing_finished)
        self.worker.start()

    def _append_log(self, message: str):
        """로그 메시지 추가"""
        self.log_area.append(message)
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_processing_finished(self, success: bool, message: str):
        """처리 완료 시 호출"""
        self.start_button.setEnabled(True)
        self.start_button.setText("🚀 요약 시작")

        if success:
            QMessageBox.information(self, "완료", f"✅ {message}")
        else:
            QMessageBox.critical(self, "오류", f"❌ {message}")


# # =============================================================================
# # 메인 애플리케이션
# # =============================================================================
#
# def main():
#     """메인 함수"""
#     app = QApplication(sys.argv)
#     app.setApplicationName(APP_TITLE)
#
#     # 폰트 설정
#     try:
#         font = QFont("맑은 고딕", 10)
#         app.setFont(font)
#     except:
#         pass  # 기본 폰트 사용
#
#     # 경로 설정
#     setup_python_path()
#
#     # 작업 디렉토리 설정
#     os.chdir(os.path.dirname(os.path.abspath(__file__)))
#
#     try:
#         # 모듈 로드
#         modules, errors = load_required_modules()
#
#         # 메인 윈도우 생성 및 실행
#         window = MainWindow(modules, errors)
#         window.show()
#
#         sys.exit(app.exec_())
#
#     except Exception as e:
#         QMessageBox.critical(
#             None, "시작 오류",
#             f"애플리케이션 시작 중 오류가 발생했습니다:\n{str(e)}\n\n"
#             "필요한 모듈들이 설치되어 있는지 확인해주세요."
#         )
#         sys.exit(1)
#
#
# if __name__ == "__main__":
#     main()