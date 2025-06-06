import sys
import os
import json
import threading
from abc import ABC, abstractmethod
from typing import Dict
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QTextEdit, QScrollArea,
                            QMessageBox, QHBoxLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# PyInstaller 환경에서 경로 설정
if getattr(sys, 'frozen', False):
    # PyInstaller로 번들된 환경
    application_path = sys._MEIPASS
    src_path = os.path.join(application_path, 'src')
else:
    # 개발 환경
    application_path = os.path.dirname(__file__)
    src_path = os.path.join(application_path, 'src')

# Python 경로에 src 디렉토리 추가
if src_path not in sys.path:
    sys.path.insert(0, src_path)
if application_path not in sys.path:
    sys.path.insert(0, application_path)

print(f"[DEBUG] Application path: {application_path}")
print(f"[DEBUG] Src path: {src_path}")
print(f"[DEBUG] Python path: {sys.path[:3]}")

# 필수 모듈들을 import 시도
UserSetting = None
VideoPipeline = None
AudioToTextPipeline = None
SummarizePipeline = None

import_errors = []
import_success = []

try:
    from user_setting import UserSetting
    import_success.append("UserSetting")
    print("[SUCCESS] UserSetting 모듈 로드 완료")
except ImportError as e:
    import_errors.append(f"UserSetting: {e}")
    print(f"[ERROR] UserSetting 로드 실패: {e}")

try:
    from video_pipeline.pipeline import VideoPipeline
    import_success.append("VideoPipeline")
    print("[SUCCESS] VideoPipeline 모듈 로드 완료")
except ImportError as e:
    import_errors.append(f"VideoPipeline: {e}")
    print(f"[ERROR] VideoPipeline 로드 실패: {e}")

try:
    from audio_pipeline.pipeline import AudioToTextPipeline
    import_success.append("AudioToTextPipeline")
    print("[SUCCESS] AudioToTextPipeline 모듈 로드 완료")
except ImportError as e:
    import_errors.append(f"AudioToTextPipeline: {e}")
    print(f"[ERROR] AudioToTextPipeline 로드 실패: {e}")

try:
    from summarize_pipeline.pipeline import SummarizePipeline
    import_success.append("SummarizePipeline")
    print("[SUCCESS] SummarizePipeline 모듈 로드 완료")
except ImportError as e:
    import_errors.append(f"SummarizePipeline: {e}")
    print(f"[ERROR] SummarizePipeline 로드 실패: {e}")

print(f"[INFO] 성공적으로 로드된 모듈: {import_success}")
if import_errors:
    print(f"[WARNING] 로드 실패한 모듈: {import_errors}")

# import 오류가 있으면 출력
if import_errors:
    print("\n[WARNING] 일부 모듈 로드 실패:")
    for error in import_errors:
        print(f"  - {error}")
    print("\n다음 명령어로 필요한 라이브러리를 설치해주세요:")
    print("pip install -r requirements.txt")


# Single Responsibility Principle: 스타일 관리 전용 클래스
class StyleManager:
    """UI 스타일을 관리하는 클래스"""

    @staticmethod
    def get_title_style() -> str:
        return """
            font-size: 24px;
            font-weight: bold;
            margin: 20px;
            color: #2c3e50;
        """

    @staticmethod
    def get_input_style() -> str:
        return """
            padding: 12px;
            font-size: 14px;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin-bottom: 10px;
            background-color: white;
        """

    @staticmethod
    def get_label_style() -> str:
        return """
            margin-top: 10px; 
            margin-bottom: 5px; 
            font-weight: bold;
            color: #34495e;
            font-size: 14px;
        """

    @staticmethod
    def get_url_input_style() -> str:
        return """
            padding: 12px;
            font-size: 14px;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin-bottom: 10px;
            min-width: 500px;
            min-height: 100px;
            background-color: white;
        """

    @staticmethod
    def get_button_style() -> str:
        return """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f648f;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """

    @staticmethod
    def get_log_style() -> str:
        return """
            background-color: #2c3e50;
            color: #ecf0f1;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #34495e;
        """


# Single Responsibility Principle: 입력 필드 데이터를 관리하는 클래스
class InputFieldData:
    """입력 필드의 데이터를 관리하는 클래스"""

    def __init__(self, label_text: str, placeholder: str, is_password: bool = False, is_multiline: bool = False):
        self.label_text = label_text
        self.placeholder = placeholder
        self.is_password = is_password
        self.is_multiline = is_multiline


# 워커 스레드 클래스
class LMSWorkerThread(QThread):
    """LMS 요약 작업을 백그라운드에서 실행하는 스레드"""
    
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, inputs: Dict[str, str]):
        super().__init__()
        self.inputs = inputs
        
    def run(self):
        try:
            self.log_signal.emit("[INFO] 🚀 LMS 요약 작업을 시작합니다...")
            
            # 필수 모듈들이 로드되었는지 확인
            if not self._check_required_modules():
                return
            
            # 환경변수 파일 생성
            self.log_signal.emit("[INFO] 📝 설정 파일을 생성하는 중...")
            self._create_env_file()
            self._create_user_settings_file()
            
            # 사용자 설정 로드
            user_setting = UserSetting()
            
            # 1. 비디오 다운로드 파이프라인
            self.log_signal.emit("[INFO] 📹 비디오 다운로드 파이프라인을 시작합니다...")
            video_pipeline = VideoPipeline(user_setting)
            urls = self._get_urls_from_input()
            self.log_signal.emit(f"[INFO] 📋 다운로드할 링크: {len(urls)}개")
            
            for i, url in enumerate(urls, 1):
                self.log_signal.emit(f"[INFO] 📥 ({i}/{len(urls)}) 다운로드 시작: {url}")
            
            downloaded_videos_path = video_pipeline.process_sync(urls)
            self.log_signal.emit(f"[SUCCESS] ✅ {len(downloaded_videos_path)}개 동영상 다운로드 완료")
            
            # 다운로드된 파일 경로 출력
            self.log_signal.emit("[INFO] 📁 다운로드된 파일들:")
            for i, filepath in enumerate(downloaded_videos_path, 1):
                self.log_signal.emit(f"   📹 ({i}) {filepath}")
            
            # 2. 오디오 파이프라인 처리
            self.log_signal.emit("[INFO] 🎵 음성을 텍스트로 변환하는 중...")
            
            # ffmpeg 경로 확인
            import shutil
            ffmpeg_path = shutil.which('ffmpeg')
            if ffmpeg_path:
                self.log_signal.emit(f"[INFO] 🔧 ffmpeg 찾음: {ffmpeg_path}")
            else:
                self.log_signal.emit("[WARNING] ⚠️ ffmpeg를 찾을 수 없습니다. PATH를 확인해주세요.")
                # PATH에 추가 시도
                possible_paths = ['/usr/local/bin', '/opt/homebrew/bin', '/usr/bin']
                for path in possible_paths:
                    if os.path.exists(os.path.join(path, 'ffmpeg')):
                        os.environ['PATH'] = path + ':' + os.environ.get('PATH', '')
                        self.log_signal.emit(f"[INFO] 🔧 ffmpeg PATH 추가: {path}")
                        break
            
            audio_pipeline = AudioToTextPipeline()
            txt_paths = []
            
            for i, filepath in enumerate(downloaded_videos_path, 1):
                try:
                    self.log_signal.emit(f"[INFO] 🎤 ({i}/{len(downloaded_videos_path)}) 텍스트 변환 중: {os.path.basename(filepath)}")
                    self.log_signal.emit(f"[INFO] 📄 원본 파일: {filepath}")
                    txt_path = audio_pipeline.process(filepath)
                    txt_paths.append(txt_path)
                    self.log_signal.emit(f"[SUCCESS] ✅ 텍스트 변환 완료: {txt_path}")
                except Exception as e:
                    self.log_signal.emit(f"[ERROR] ❌ 텍스트 변환 실패 ({os.path.basename(filepath)}): {e}")
                    self.log_signal.emit(f"[DEBUG] 오류 상세: {str(e)}")
            
            # 변환된 텍스트 파일 목록
            if txt_paths:
                self.log_signal.emit("[INFO] 📄 변환된 텍스트 파일들:")
                for i, txt_path in enumerate(txt_paths, 1):
                    self.log_signal.emit(f"   📝 ({i}) {txt_path}")
            
            # 3. 요약 파이프라인 처리
            self.log_signal.emit("[INFO] 🤖 AI 요약을 생성하는 중...")
            summarized_txt_paths = []
            summarize_pipeline = SummarizePipeline()
            
            for i, txt_path in enumerate(txt_paths, 1):
                try:
                    self.log_signal.emit(f"[INFO] 📝 ({i}/{len(txt_paths)}) 요약 생성 중: {os.path.basename(txt_path)}")
                    self.log_signal.emit(f"[INFO] 📄 입력 파일: {txt_path}")
                    summarized_txt_path = summarize_pipeline.process(txt_path)
                    summarized_txt_paths.append(summarized_txt_path)
                    self.log_signal.emit(f"[SUCCESS] ✅ 요약 완료: {summarized_txt_path}")
                except Exception as e:
                    self.log_signal.emit(f"[ERROR] ❌ 요약 생성 실패 ({os.path.basename(txt_path)}): {e}")
                    self.log_signal.emit(f"[DEBUG] 오류 상세: {str(e)}")
            
            # 완료 메시지
            self.log_signal.emit("\n" + "="*50)
            self.log_signal.emit("[SUCCESS] 🎉 모든 작업이 완료되었습니다!")
            
            if downloaded_videos_path:
                self.log_signal.emit("📹 다운로드된 동영상:")
                for path in downloaded_videos_path:
                    self.log_signal.emit(f"   📄 {path}")
            
            if txt_paths:
                self.log_signal.emit("📝 변환된 텍스트:")
                for path in txt_paths:
                    self.log_signal.emit(f"   📄 {path}")
            
            if summarized_txt_paths:
                self.log_signal.emit("🤖 요약된 파일들:")
                for path in summarized_txt_paths:
                    self.log_signal.emit(f"   📄 {path}")
            
            # 저장 위치 안내
            if downloaded_videos_path or txt_paths or summarized_txt_paths:
                downloads_dir = resource_path("downloads")
                self.log_signal.emit(f"\n📁 모든 파일이 저장된 위치: {downloads_dir}")
                self.log_signal.emit("💡 Finder에서 확인: open downloads/")
            
            self.log_signal.emit("="*50)
            
            total_files = len(downloaded_videos_path) + len(txt_paths) + len(summarized_txt_paths)
            self.finished_signal.emit(True, f"총 {total_files}개 파일 처리 완료")
            
        except Exception as e:
            self.log_signal.emit(f"[ERROR] ❌ 작업 중 오류 발생: {str(e)}")
            import traceback
            self.log_signal.emit(f"[DEBUG] 상세 오류:\n{traceback.format_exc()}")
            self.finished_signal.emit(False, str(e))
    
    def _check_required_modules(self) -> bool:
        """필수 모듈들이 로드되었는지 확인"""
        missing_modules = []
        
        if UserSetting is None:
            missing_modules.append("UserSetting")
        if VideoPipeline is None:
            missing_modules.append("VideoPipeline") 
        if AudioToTextPipeline is None:
            missing_modules.append("AudioToTextPipeline")
        if SummarizePipeline is None:
            missing_modules.append("SummarizePipeline")
            
        if missing_modules:
            self.log_signal.emit(f"[ERROR] ❌ 필수 모듈들이 로드되지 않았습니다: {', '.join(missing_modules)}")
            self.log_signal.emit("[ERROR] ❌ 다음 명령어로 필요한 라이브러리를 설치해주세요:")
            self.log_signal.emit("[ERROR] ❌ pip install -r requirements.txt")
            self.finished_signal.emit(False, f"필수 모듈 로드 실패: {', '.join(missing_modules)}")
            return False
            
        return True
    
    def _create_env_file(self):
        """환경변수 파일 생성"""
        env_content = f"""USERID={self.inputs.get('student_id', '')}
PASSWORD={self.inputs.get('password', '')}
GOOGLE_API_KEY={self.inputs.get('api_key', '')}
"""
        with open(resource_path('.env'), 'w', encoding='utf-8') as f:
            f.write(env_content)
    
    def _create_user_settings_file(self):
        """사용자 설정 파일 생성"""
        urls = self._get_urls_from_input()
        settings = {"video": urls}
        
        with open(resource_path('user_settings.json'), 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    
    def _get_urls_from_input(self) -> list[str]:
        """입력에서 URL 목록 추출"""
        url_text = self.inputs.get('urls', '').strip()
        if not url_text:
            return []
        
        # 여러 줄로 입력된 URL들을 분리
        urls = [url.strip() for url in url_text.split('\n') if url.strip()]
        return urls


# Open/Closed Principle: 입력 처리를 위한 추상 인터페이스
class InputProcessor(ABC):
    """입력 데이터 처리를 위한 추상 클래스"""

    @abstractmethod
    def process_inputs(self, inputs: Dict[str, str]) -> None:
        pass


# Open/Closed Principle: 구체적인 입력 처리 구현
class LMSInputProcessor(InputProcessor):
    """LMS 요약 작업을 실행하는 처리기"""

    def __init__(self, parent_widget):
        self.parent_widget = parent_widget

    def process_inputs(self, inputs: Dict[str, str]) -> None:
        # 필수 모듈 확인
        if not self._check_modules_available():
            return
            
        # 입력값 검증
        if not self._validate_inputs(inputs):
            return
        
        # 워커 스레드 시작
        self.parent_widget.start_processing(inputs)

    def _check_modules_available(self) -> bool:
        """필수 모듈들이 사용 가능한지 확인"""
        if any(module is None for module in [UserSetting, VideoPipeline, AudioToTextPipeline, SummarizePipeline]):
            QMessageBox.critical(
                self.parent_widget.window, 
                "모듈 오류", 
                "❌ 필수 모듈들이 로드되지 않았습니다.\n\n"
                "다음 명령어를 실행하여 필요한 라이브러리를 설치해주세요:\n"
                "pip install -r requirements.txt\n\n"
                "그리고 애플리케이션을 다시 시작해주세요."
            )
            return False
        return True

    def _validate_inputs(self, inputs: Dict[str, str]) -> bool:
        """입력값 유효성 검사"""
        if not inputs.get('student_id'):
            QMessageBox.warning(self.parent_widget.window, "입력 오류", "학번을 입력해주세요.")
            return False
        
        if not inputs.get('password'):
            QMessageBox.warning(self.parent_widget.window, "입력 오류", "비밀번호를 입력해주세요.")
            return False
        
        if not inputs.get('api_key'):
            QMessageBox.warning(self.parent_widget.window, "입력 오류", "Google API 키를 입력해주세요.")
            return False
        
        if not inputs.get('urls'):
            QMessageBox.warning(self.parent_widget.window, "입력 오류", "강의 URL을 입력해주세요.")
            return False
        
        return True


# Single Responsibility Principle: 입력 필드 생성을 담당하는 팩토리
class InputFieldFactory:
    """입력 필드 위젯들을 생성하는 팩토리 클래스"""

    @staticmethod
    def create_label(field_data: InputFieldData) -> QLabel:
        label = QLabel(field_data.label_text)
        label.setStyleSheet(StyleManager.get_label_style())
        return label

    @staticmethod
    def create_input(field_data: InputFieldData):
        if field_data.is_multiline:
            input_field = QTextEdit()
            input_field.setPlaceholderText(field_data.placeholder)
            input_field.setStyleSheet(StyleManager.get_url_input_style())
            input_field.setMaximumHeight(120)
        else:
            input_field = QLineEdit()
            input_field.setPlaceholderText(field_data.placeholder)
            input_field.setStyleSheet(StyleManager.get_input_style())
            
            if field_data.is_password:
                input_field.setEchoMode(QLineEdit.Password)

        return input_field


# Single Responsibility Principle: UI 구성요소들을 관리하는 클래스
class UIComponents:
    """UI 구성요소들을 관리하는 클래스"""

    def __init__(self):
        self.input_fields = {}
        self.layout = QVBoxLayout()
        self.log_area = None
        self._setup_input_fields_config()

    def _setup_input_fields_config(self) -> None:
        """입력 필드 설정을 초기화"""
        self.field_configs = {
            'student_id': InputFieldData("📚 학번:", "예: 20201234"),
            'password': InputFieldData("🔒 비밀번호:", "Canvas LMS 비밀번호", is_password=True),
            'api_key': InputFieldData("🔑 Google API 키:", "sk-... (Google API 키를 입력하세요)"),
            'urls': InputFieldData("🎬 강의 URL 목록:", "https://canvas.ssu.ac.kr/courses/...\n(여러 URL은 각각 새 줄에 입력)", is_multiline=True)
        }

    def create_title(self) -> QLabel:
        """제목 라벨 생성"""
        title_label = QLabel("🎓 LMS 강의 자동 요약 도구")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(StyleManager.get_title_style())
        return title_label

    def create_input_fields(self) -> None:
        """모든 입력 필드들을 생성하고 레이아웃에 추가"""
        for field_name, field_data in self.field_configs.items():
            # 라벨 생성 및 추가
            label = InputFieldFactory.create_label(field_data)
            self.layout.addWidget(label)

            # 입력 필드 생성 및 추가
            input_field = InputFieldFactory.create_input(field_data)
            self.input_fields[field_name] = input_field
            self.layout.addWidget(input_field)

    def create_log_area(self) -> QTextEdit:
        """로그 영역 생성"""
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet(StyleManager.get_log_style())
        self.log_area.setMaximumHeight(300)
        self.log_area.setPlainText("📋 작업 로그가 여기에 표시됩니다...\n")
        return self.log_area

    def create_button(self, text: str, callback) -> QPushButton:
        """버튼 생성"""
        button = QPushButton(text)
        button.setStyleSheet(StyleManager.get_button_style())
        button.clicked.connect(callback)
        return button

    def get_input_values(self) -> Dict[str, str]:
        """모든 입력 필드의 값을 반환"""
        values = {}
        for field_name, field_widget in self.input_fields.items():
            if hasattr(field_widget, 'toPlainText'):  # QTextEdit
                values[field_name] = field_widget.toPlainText()
            else:  # QLineEdit
                values[field_name] = field_widget.text()
        return values

    def append_log(self, message: str):
        """로그 메시지 추가"""
        if self.log_area:
            self.log_area.append(message)
            # 자동 스크롤
            scrollbar = self.log_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())


# Dependency Inversion Principle: 높은 수준의 모듈이 낮은 수준의 모듈에 의존하지 않도록
class LectureToolApplication:
    """강의 도구 애플리케이션의 메인 클래스"""

    def __init__(self, input_processor: InputProcessor):
        self.input_processor = input_processor
        self.ui_components = UIComponents()
        self.window = None
        self.start_button = None
        self.worker_thread = None
        self._setup_window()

    def _setup_window(self) -> None:
        """메인 윈도우 설정"""
        self.window = QWidget()
        self.window.setWindowTitle("LMS 강의 자동 요약 도구 v1.0")
        self.window.resize(700, 800)
        self.window.setStyleSheet("background-color: #ecf0f1;")

    def _setup_ui(self) -> None:
        """UI 구성요소들을 설정"""
        # 제목 추가
        title = self.ui_components.create_title()
        self.ui_components.layout.addWidget(title)

        # 안내 메시지
        info_label = QLabel("📖 숭실대학교 Canvas LMS 강의 동영상을 자동으로 다운로드하고 AI로 요약합니다.")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-bottom: 20px;")
        self.ui_components.layout.addWidget(info_label)

        # 모듈 상태 표시
        self._add_module_status()

        # 입력 필드들 생성
        self.ui_components.create_input_fields()

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        # 시작 버튼 생성
        self.start_button = self.ui_components.create_button("🚀 요약 시작", self._handle_start_button_click)
        button_layout.addWidget(self.start_button)

        self.ui_components.layout.addLayout(button_layout)

        # 로그 영역 추가
        log_label = QLabel("📋 작업 로그:")
        log_label.setStyleSheet(StyleManager.get_label_style())
        self.ui_components.layout.addWidget(log_label)
        
        log_area = self.ui_components.create_log_area()
        self.ui_components.layout.addWidget(log_area)

        # 윈도우에 레이아웃 설정
        self.window.setLayout(self.ui_components.layout)

    def _add_module_status(self):
        """모듈 로드 상태 표시"""
        modules_status = []
        if UserSetting is not None:
            modules_status.append("✅ UserSetting")
        else:
            modules_status.append("❌ UserSetting")
            
        if VideoPipeline is not None:
            modules_status.append("✅ VideoPipeline")
        else:
            modules_status.append("❌ VideoPipeline")
            
        if AudioToTextPipeline is not None:
            modules_status.append("✅ AudioToTextPipeline")
        else:
            modules_status.append("❌ AudioToTextPipeline")
            
        if SummarizePipeline is not None:
            modules_status.append("✅ SummarizePipeline")
        else:
            modules_status.append("❌ SummarizePipeline")

        status_text = " | ".join(modules_status)
        status_label = QLabel(f"모듈 상태: {status_text}")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("color: #7f8c8d; font-size: 10px; margin-bottom: 15px;")
        self.ui_components.layout.addWidget(status_label)

    def _handle_start_button_click(self) -> None:
        """시작 버튼 클릭 처리"""
        inputs = self.ui_components.get_input_values()
        self.input_processor.process_inputs(inputs)

    def start_processing(self, inputs: Dict[str, str]):
        """백그라운드 처리 시작"""
        # 버튼 비활성화
        self.start_button.setEnabled(False)
        self.start_button.setText("⏳ 처리 중...")
        
        # 로그 초기화
        self.ui_components.log_area.clear()
        
        # 워커 스레드 시작
        self.worker_thread = LMSWorkerThread(inputs)
        self.worker_thread.log_signal.connect(self.ui_components.append_log)
        self.worker_thread.finished_signal.connect(self._on_processing_finished)
        self.worker_thread.start()

    def _on_processing_finished(self, success: bool, message: str):
        """처리 완료 시 호출"""
        # 버튼 다시 활성화
        self.start_button.setEnabled(True)
        self.start_button.setText("🚀 요약 시작")
        
        # 결과 메시지 표시
        if success:
            QMessageBox.information(self.window, "완료", f"✅ 작업이 완료되었습니다!\n{message}")
        else:
            QMessageBox.critical(self.window, "오류", f"❌ 작업 중 오류가 발생했습니다:\n{message}")

    def run(self) -> None:
        """애플리케이션 실행"""
        self._setup_ui()
        self.window.show()


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    app.setApplicationName("LMS 강의 자동 요약 도구")
    
    # 폰트 설정 (시스템 기본 폰트 사용)
    try:
        font = QFont("맑은 고딕", 10)
        app.setFont(font)
    except:
        # 맑은 고딕이 없으면 시스템 기본 폰트 사용
        pass

    # 현재 디렉토리를 작업 디렉토리로 설정
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    try:
        # 필수 모듈들이 로드되었는지 확인
        if any(module is None for module in [UserSetting, VideoPipeline, AudioToTextPipeline, SummarizePipeline]):
            missing_modules = []
            if UserSetting is None: missing_modules.append("UserSetting")
            if VideoPipeline is None: missing_modules.append("VideoPipeline")
            if AudioToTextPipeline is None: missing_modules.append("AudioToTextPipeline")
            if SummarizePipeline is None: missing_modules.append("SummarizePipeline")
            
            error_msg = (
                f"필수 모듈들이 로드되지 않았습니다: {', '.join(missing_modules)}\n\n"
                "다음 명령어를 실행하여 필요한 라이브러리를 설치해주세요:\n"
                "pip install -r requirements.txt\n\n"
                "그리고 애플리케이션을 다시 시작해주세요."
            )
            
            QMessageBox.critical(None, "모듈 로드 오류", error_msg)
            print(f"\n[ERROR] {error_msg}")
        
        # Dependency Injection: 구체적인 구현체를 주입
        lecture_app = LectureToolApplication(None)  # 임시로 None
        input_processor = LMSInputProcessor(lecture_app)
        lecture_app.input_processor = input_processor
        
        lecture_app.run()
        
        sys.exit(app.exec_())
        
    except Exception as e:
        QMessageBox.critical(None, "시작 오류", f"애플리케이션 시작 중 오류가 발생했습니다:\n{str(e)}\n\n필요한 모듈들이 설치되어 있는지 확인해주세요.")
        sys.exit(1)


if __name__ == "__main__":
    main() 