"""
메인 윈도우 클래스
"""

from typing import Dict, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox,
    QFileDialog, QPushButton
)
from PyQt5.QtCore import Qt

from src.gui.config.constants import APP_TITLE, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, Messages
from src.gui.config.styles import StyleSheet
from src.gui.config.settings import INPUT_FIELD_CONFIGS
from src.gui.core.validators import InputValidator
from src.gui.core.module_loader import check_required_modules
from src.gui.core.file_manager import (
    ensure_downloads_directory, set_downloads_directory,
    get_default_downloads_dir
)
from src.gui.ui.components.input_field import InputField
from src.gui.ui.components.log_area import LogArea
from src.gui.ui.components.buttons import ProcessingButton, ClearButton
from src.gui.workers.processing_worker import ProcessingWorker


class MainWindow(QWidget):
    """메인 윈도우 클래스"""

    def __init__(self, modules: Dict, module_errors: List[str]):
        super().__init__()

        # 데이터 저장
        self.modules = modules
        self.module_errors = module_errors

        # UI 컴포넌트들
        self.input_fields = {}
        self.log_area = None
        self.start_button = None
        self.clear_button = None
        self.worker = None
        self.path_button = None

        # 윈도우 설정 및 UI 구성
        self._setup_window()
        self._setup_ui()
        self._check_module_status()

    def _setup_window(self):
        """윈도우 기본 설정"""
        self.setWindowTitle(f"{APP_TITLE} {APP_VERSION}")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setStyleSheet(StyleSheet.main_window())

    def _setup_ui(self):
        """UI 구성요소 설정"""
        main_layout = QVBoxLayout()

        # 헤더 섹션
        self._create_header_section(main_layout)

        # 저장 경로 섹션
        self._create_path_section(main_layout)

        # 입력 필드 섹션
        self._create_input_section(main_layout)

        # 버튼 섹션
        self._create_button_section(main_layout)

        # 로그 섹션
        self._create_log_section(main_layout)

        self.setLayout(main_layout)

    def _create_header_section(self, layout: QVBoxLayout):
        """헤더 섹션 생성"""
        # 제목
        title = QLabel(f"🎓 {APP_TITLE}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(StyleSheet.title())
        layout.addWidget(title)

        # 설명
        description = QLabel("📖 숭실대학교 LMS 강의 동영상을 다운로드하고 AI로 요약합니다.")
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet(StyleSheet.subtitle())
        layout.addWidget(description)

    def _create_path_section(self, layout: QVBoxLayout):
        """저장 경로 설정 섹션 생성"""
        path_layout = QHBoxLayout()
        
        # 라벨
        path_label = QLabel("📁 저장 경로:")
        path_label.setStyleSheet(StyleSheet.label())
        path_layout.addWidget(path_label)
        
        # 현재 경로 표시
        current_path = ensure_downloads_directory()
        path_value = QLabel(current_path)
        path_value.setStyleSheet(StyleSheet.path_value())
        path_value.setWordWrap(True)
        path_layout.addWidget(path_value, stretch=1)
        
        # 경로 변경 버튼
        self.path_button = QPushButton("경로 변경")
        self.path_button.setStyleSheet(StyleSheet.button())
        self.path_button.clicked.connect(self._change_download_path)
        path_layout.addWidget(self.path_button)
        
        layout.addLayout(path_layout)

    def _change_download_path(self):
        """다운로드 경로 변경"""
        current_path = ensure_downloads_directory()
        new_path = QFileDialog.getExistingDirectory(
            self,
            "저장 경로 선택",
            current_path,
            QFileDialog.ShowDirsOnly
        )
        
        if new_path:
            try:
                set_downloads_directory(new_path)
                self.log_area.append_message(f"✅ 저장 경로가 변경되었습니다: {new_path}")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "경로 변경 오류",
                    f"저장 경로 변경 중 오류가 발생했습니다:\n{str(e)}"
                )

    def _create_input_section(self, layout: QVBoxLayout):
        """입력 필드 섹션 생성"""
        for field_name, config in INPUT_FIELD_CONFIGS.items():
            field = InputField(config)
            self.input_fields[field_name] = field

            layout.addWidget(field.label)
            layout.addWidget(field.widget)

    def _create_button_section(self, layout: QVBoxLayout):
        """버튼 섹션 생성"""
        button_layout = QHBoxLayout()

        # 시작 버튼
        self.start_button = ProcessingButton()
        self.start_button.clicked.connect(self._handle_start_processing)
        button_layout.addWidget(self.start_button)

        # 초기화 버튼
        self.clear_button = ClearButton()
        self.clear_button.clicked.connect(self._handle_clear_inputs)
        button_layout.addWidget(self.clear_button)

        layout.addLayout(button_layout)

    def _create_log_section(self, layout: QVBoxLayout):
        """로그 섹션 생성"""
        self.log_area = LogArea()
        layout.addWidget(self.log_area.label)
        layout.addWidget(self.log_area.text_area)

    def _check_module_status(self):
        """모듈 상태 확인 및 경고 표시"""
        if self.module_errors:
            self.log_area.append_message("⚠️ 일부 모듈 로드 실패:")
            for error in self.module_errors:
                self.log_area.append_message(f"   - {error}")
            self.log_area.append_message(Messages.INSTALL_REQUIREMENTS)

    def _handle_start_processing(self):
        """처리 시작 버튼 클릭 핸들러"""
        # 입력값 수집
        inputs = self._collect_input_values()

        # 입력값 검증
        if not self._validate_inputs(inputs):
            return

        # 모듈 상태 확인
        if not self._check_modules_ready():
            return

        # 처리 시작
        self._start_background_processing(inputs)

    def _handle_clear_inputs(self):
        """입력 필드 초기화 버튼 클릭 핸들러"""
        reply = QMessageBox.question(
            self, "확인",
            "모든 입력 필드를 초기화하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            for field in self.input_fields.values():
                field.clear()
            self.log_area.clear()

    def _collect_input_values(self) -> Dict[str, str]:
        """모든 입력 필드의 값 수집"""
        return {
            field_name: field.get_value()
            for field_name, field in self.input_fields.items()
        }

    def _validate_inputs(self, inputs: Dict[str, str]) -> bool:
        """입력값 유효성 검사"""
        valid, error_message = InputValidator.validate_all_inputs(inputs)

        if not valid:
            QMessageBox.warning(self, "입력 오류", error_message)
            return False

        return True

    def _check_modules_ready(self) -> bool:
        """필수 모듈들이 준비되었는지 확인"""
        all_loaded, missing_modules = check_required_modules(self.modules)

        if not all_loaded:
            QMessageBox.critical(
                self, "모듈 오류",
                f"{Messages.MODULE_LOAD_ERROR}: {', '.join(missing_modules)}\n\n"
                f"{Messages.INSTALL_REQUIREMENTS}"
            )
            return False

        return True

    def _start_background_processing(self, inputs: Dict[str, str]):
        """백그라운드 처리 시작"""
        # UI 상태 변경
        self.start_button.start_processing()
        self.clear_button.setEnabled(False)
        self._set_input_fields_enabled(False)

        # 로그 초기화
        self.log_area.clear()

        # 워커 스레드 시작
        self.worker = ProcessingWorker(inputs, self.modules)
        self.worker.log_message.connect(self.log_area.append_message)
        self.worker.processing_finished.connect(self._on_processing_finished)
        self.worker.start()

    def _set_input_fields_enabled(self, enabled: bool):
        """모든 입력 필드 활성화/비활성화"""
        for field in self.input_fields.values():
            field.set_enabled(enabled)

    def _on_processing_finished(self, success: bool, message: str):
        """처리 완료 시 호출되는 콜백"""
        # UI 상태 복원
        self.start_button.stop_processing()
        self.clear_button.setEnabled(True)
        self._set_input_fields_enabled(True)

        # 결과 메시지 표시
        if success:
            QMessageBox.information(
                self, "완료",
                f"✅ 작업이 완료되었습니다!\n{message}"
            )
        else:
            QMessageBox.critical(
                self, "오류",
                f"❌ 작업 중 오류가 발생했습니다:\n{message}"
            )

        # 워커 정리
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    def closeEvent(self, event):
        """윈도우 종료 시 호출"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "확인",
                "작업이 진행 중입니다. 정말 종료하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.worker.terminate()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()