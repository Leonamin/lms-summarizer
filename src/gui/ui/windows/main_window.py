"""
메인 윈도우 클래스
"""

import subprocess
import sys
from typing import Dict, List

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox,
    QFileDialog, QCheckBox, QSplitter,
    QScrollArea, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt

from src.gui.config.constants import (
    APP_TITLE, APP_VERSION,
    WINDOW_WIDTH, WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT,
    Messages, EMOJI_PROCESSING
)
from src.gui.config.styles import StyleSheet
from src.gui.config.settings import INPUT_FIELD_CONFIGS
from src.gui.core.validators import InputValidator
from src.gui.core.module_loader import check_required_modules
from src.gui.core.file_manager import (
    ensure_downloads_directory, set_downloads_directory,
    save_user_inputs, load_user_inputs
)
from src.gui.ui.components.input_field import InputField
from src.gui.ui.components.log_area import LogArea
from src.gui.ui.components.buttons import ProcessingButton, ClearButton, AppButton
from src.gui.ui.dialogs.progress_modal import ProcessingModal
from src.gui.workers.processing_worker import ProcessingWorker


class MainWindow(QWidget):
    """메인 윈도우 클래스"""

    def __init__(self, modules: Dict, module_errors: List[str]):
        super().__init__()

        self.modules = modules
        self.module_errors = module_errors

        self.input_fields: Dict[str, InputField] = {}
        self.log_area: LogArea = None
        self.start_button: ProcessingButton = None
        self.clear_button: ClearButton = None
        self.save_video_checkbox: QCheckBox = None
        self.worker: ProcessingWorker = None
        self.modal: ProcessingModal = None
        self.path_value_label: QLabel = None

        self._setup_window()
        self._setup_ui()
        self._load_saved_inputs()
        self._check_module_status()

    # ── 윈도우 초기 설정 ──────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle(f"{APP_TITLE} {APP_VERSION}")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.setStyleSheet(StyleSheet.main_window())

    # ── UI 구성 ────────────────────────────────────────────────────

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(8)

        self._create_header_section(main_layout)
        self._create_path_section(main_layout)

        # QSplitter: 입력 폼(상단) / 로그(하단)
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)

        splitter.addWidget(self._build_form_widget())
        splitter.addWidget(self._build_log_widget())

        # 초기 비율: 폼 70%, 로그 30%
        splitter.setSizes([380, 160])

        main_layout.addWidget(splitter, stretch=1)
        self.setLayout(main_layout)

    def _create_header_section(self, layout: QVBoxLayout):
        title = QLabel(f"🎓 {APP_TITLE}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(StyleSheet.title())
        layout.addWidget(title)

        desc = QLabel("📖 숭실대학교 LMS 강의 동영상을 다운로드하고 AI로 요약합니다.")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(StyleSheet.subtitle())
        layout.addWidget(desc)

    def _create_path_section(self, layout: QVBoxLayout):
        path_layout = QHBoxLayout()
        path_layout.setSpacing(6)

        path_label = QLabel("📁 저장 경로:")
        path_label.setStyleSheet(StyleSheet.label())
        path_label.setFixedWidth(72)
        path_layout.addWidget(path_label)

        current_path = ensure_downloads_directory()
        self.path_value_label = QLabel(current_path)
        self.path_value_label.setStyleSheet(StyleSheet.path_value())
        self.path_value_label.setWordWrap(True)
        path_layout.addWidget(self.path_value_label, stretch=1)

        open_btn = AppButton("📂 열기", "outline")
        open_btn.clicked.connect(self._open_in_finder)
        path_layout.addWidget(open_btn)

        change_btn = AppButton("경로 변경", "outline")
        change_btn.clicked.connect(self._change_download_path)
        path_layout.addWidget(change_btn)

        layout.addLayout(path_layout)

    def _build_form_widget(self) -> QScrollArea:
        """입력 폼 영역 (스크롤 가능한 카드)"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        card = QFrame()
        card.setStyleSheet(StyleSheet.card())
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(4)

        # 입력 필드 생성
        for field_name, config in INPUT_FIELD_CONFIGS.items():
            field = InputField(config)
            self.input_fields[field_name] = field

            card_layout.addWidget(field.label)
            card_layout.addWidget(field.widget)

            if field.caps_lock_label is not None:
                card_layout.addWidget(field.caps_lock_label)

        # URL 입력창이 세로 방향으로 늘어나도록 설정
        urls_widget = self.input_fields['urls'].widget
        urls_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        urls_widget.setMinimumHeight(80)

        # 옵션 체크박스
        self.save_video_checkbox = QCheckBox("📹 처리 완료 후 원본 동영상 보관 (미선택 시 자동 삭제)")
        self.save_video_checkbox.setStyleSheet(StyleSheet.checkbox())
        self.save_video_checkbox.setChecked(False)
        card_layout.addWidget(self.save_video_checkbox)

        # 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        self.start_button = ProcessingButton()
        self.start_button.clicked.connect(self._handle_start_processing)
        btn_layout.addWidget(self.start_button)

        self.clear_button = ClearButton()
        self.clear_button.clicked.connect(self._handle_clear_inputs)
        btn_layout.addWidget(self.clear_button)

        card_layout.addLayout(btn_layout)
        card_layout.addStretch()

        scroll.setWidget(card)
        return scroll

    def _build_log_widget(self) -> QWidget:
        """로그 영역"""
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 4, 0, 0)
        log_layout.setSpacing(2)

        self.log_area = LogArea()
        log_layout.addWidget(self.log_area.label)
        log_layout.addWidget(self.log_area.text_area, stretch=1)

        return log_container

    # ── 이벤트 핸들러 ──────────────────────────────────────────────

    def _change_download_path(self):
        current_path = ensure_downloads_directory()
        new_path = QFileDialog.getExistingDirectory(
            self, "저장 경로 선택", current_path, QFileDialog.ShowDirsOnly
        )
        if new_path:
            try:
                set_downloads_directory(new_path)
                self.path_value_label.setText(new_path)
                self.log_area.append_message(f"✅ 저장 경로 변경: {new_path}")
            except Exception as e:
                QMessageBox.critical(self, "경로 변경 오류", f"저장 경로 변경 중 오류:\n{str(e)}")

    def _open_in_finder(self):
        path = ensure_downloads_directory()
        if sys.platform == 'darwin':
            subprocess.Popen(['open', path])
        elif sys.platform == 'win32':
            subprocess.Popen(['explorer', path])
        else:
            subprocess.Popen(['xdg-open', path])

    def _handle_start_processing(self):
        if self.start_button.is_processing:
            self._handle_stop_processing()
            return

        inputs = self._collect_input_values()
        if not self._validate_inputs(inputs):
            return
        if not self._check_modules_ready():
            return

        self._start_background_processing(inputs)

    def _handle_stop_processing(self):
        reply = QMessageBox.question(
            self, "확인",
            "진행 중인 작업을 중지하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes and self.worker:
            self.worker.request_cancel()
            self.log_area.append_message("⚠️ 작업 중지를 요청했습니다...")
            self.start_button.setEnabled(False)
            self.start_button.setText(f"{EMOJI_PROCESSING} 중지 중...")

    def _handle_clear_inputs(self):
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

    # ── 처리 시작 / 완료 ───────────────────────────────────────────

    def _start_background_processing(self, inputs: Dict[str, str]):
        save_user_inputs(inputs)

        self.start_button.start_processing()
        self.clear_button.setEnabled(False)
        self._set_input_fields_enabled(False)
        self.log_area.clear()

        save_video_dir = ensure_downloads_directory() if self.save_video_checkbox.isChecked() else None

        self.worker = ProcessingWorker(inputs, self.modules, save_video_dir=save_video_dir)
        self.worker.log_message.connect(self.log_area.append_message)
        self.worker.processing_finished.connect(self._on_processing_finished)

        # 모달 생성 및 연결
        self.modal = ProcessingModal(self)
        self.worker.log_message.connect(self.modal.append_log)
        self.worker.step_changed.connect(self.modal.update_step)
        self.worker.progress_updated.connect(self.modal.update_progress)
        self.modal.stop_requested.connect(self._on_modal_stop_requested)

        self.worker.start()
        self.modal.show()

    def _on_modal_stop_requested(self):
        """모달에서 중지 버튼 클릭"""
        if self.worker:
            self.worker.request_cancel()
            self.log_area.append_message("⚠️ 작업 중지를 요청했습니다...")

    def _on_processing_finished(self, success: bool, message: str):
        # UI 상태 복원
        self.start_button.stop_processing()
        self.clear_button.setEnabled(True)
        self._set_input_fields_enabled(True)

        # 모달 상태 업데이트
        if self.modal:
            if success:
                self.modal.mark_complete()
            else:
                self.modal.mark_cancelled()

        # 결과 메시지 표시 (취소는 조용히 처리)
        if success:
            if self.modal:
                self.modal.accept()
            QMessageBox.information(self, "완료", f"✅ 작업이 완료되었습니다!\n{message}")
        elif "취소" not in message:
            QMessageBox.critical(self, "오류", f"❌ 작업 중 오류:\n{message}")

        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    # ── 유틸리티 ───────────────────────────────────────────────────

    def _collect_input_values(self) -> Dict[str, str]:
        return {name: field.get_value() for name, field in self.input_fields.items()}

    def _validate_inputs(self, inputs: Dict[str, str]) -> bool:
        valid, error_message = InputValidator.validate_all_inputs(inputs)
        if not valid:
            QMessageBox.warning(self, "입력 오류", error_message)
            return False
        return True

    def _check_modules_ready(self) -> bool:
        all_loaded, missing = check_required_modules(self.modules)
        if not all_loaded:
            QMessageBox.critical(
                self, "모듈 오류",
                f"{Messages.MODULE_LOAD_ERROR}: {', '.join(missing)}\n\n{Messages.INSTALL_REQUIREMENTS}"
            )
            return False
        return True

    def _set_input_fields_enabled(self, enabled: bool):
        for field in self.input_fields.values():
            field.set_enabled(enabled)

    def _check_module_status(self):
        if self.module_errors:
            self.log_area.append_message("⚠️ 일부 모듈 로드 실패:")
            for error in self.module_errors:
                self.log_area.append_message(f"   - {error}")
            self.log_area.append_message(Messages.INSTALL_REQUIREMENTS)

    def _load_saved_inputs(self):
        saved = load_user_inputs()
        for field_name, value in saved.items():
            if field_name in self.input_fields and value:
                self.input_fields[field_name].set_value(value)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "확인",
                "작업이 진행 중입니다. 정말 종료하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.worker.request_cancel()
                self.worker.wait(5000)
                if self.worker.isRunning():
                    self.worker.terminate()
                    self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
