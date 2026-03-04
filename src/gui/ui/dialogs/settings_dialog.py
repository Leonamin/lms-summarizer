"""
설정 다이얼로그 - 요약 프롬프트, Chrome 경로 설정
"""

import os

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QLineEdit, QFileDialog, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt

from src.gui.config.constants import Colors
from src.gui.config.styles import StyleSheet
from src.gui.ui.components.buttons import AppButton
from src.gui.ui.components.icons import AppIcons
from src.gui.core.file_manager import (
    DEFAULT_PROMPT,
    get_summary_prompt, set_summary_prompt,
    get_chrome_path, set_chrome_path, detect_chrome_paths,
)


class SettingsDialog(QDialog):
    """요약 프롬프트 및 Chrome 경로를 설정하는 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("설정")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setStyleSheet(StyleSheet.modal_window())
        self._setup_ui()
        self._load_current_settings()

    # ── UI 구성 ────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        # 제목
        title = AppIcons.label('settings', '설정', icon_size=18)
        title.setStyleSheet(StyleSheet.modal_title())
        layout.addWidget(title)
        layout.addWidget(self._make_divider())

        # 섹션 1: 요약 프롬프트
        self._build_prompt_section(layout)
        layout.addWidget(self._make_divider())

        # 섹션 2: Chrome 경로
        self._build_chrome_section(layout)
        layout.addWidget(self._make_divider())

        # 하단 버튼
        self._build_button_section(layout)

        self.setLayout(layout)

    def _build_prompt_section(self, layout: QVBoxLayout):
        label = AppIcons.label('prompt', '요약 프롬프트:')
        label.setStyleSheet(StyleSheet.label())
        layout.addWidget(label)

        desc = QLabel("AI 요약 시 사용되는 프롬프트를 수정할 수 있습니다.")
        desc.setStyleSheet(f"color: {Colors.TEXT_LIGHT}; font-size: 11px;")
        layout.addWidget(desc)

        self._prompt_edit = QTextEdit()
        self._prompt_edit.setStyleSheet(StyleSheet.multiline_input())
        self._prompt_edit.setMinimumHeight(80)
        self._prompt_edit.setMaximumHeight(150)
        layout.addWidget(self._prompt_edit)

        reset_btn = AppButton("기본값 복원", "text")
        reset_btn.setIcon(AppIcons.icon('reset'))
        reset_btn.clicked.connect(self._reset_prompt)
        layout.addWidget(reset_btn, alignment=Qt.AlignLeft)

    def _build_chrome_section(self, layout: QVBoxLayout):
        label = AppIcons.label('chrome', 'Chrome 브라우저 경로:')
        label.setStyleSheet(StyleSheet.label())
        layout.addWidget(label)

        desc = QLabel("LMS 영상 재생에 사용할 Chrome 실행 파일 경로입니다.")
        desc.setStyleSheet(f"color: {Colors.TEXT_LIGHT}; font-size: 11px;")
        layout.addWidget(desc)

        # 경로 입력 + 찾아보기 버튼
        path_row = QHBoxLayout()
        self._chrome_path_edit = QLineEdit()
        self._chrome_path_edit.setStyleSheet(StyleSheet.input_field())
        self._chrome_path_edit.setPlaceholderText("Chrome 실행 파일 경로")
        path_row.addWidget(self._chrome_path_edit)

        browse_btn = AppButton("찾아보기...", "outline")
        browse_btn.setIcon(AppIcons.icon('browse'))
        browse_btn.setFixedWidth(120)
        browse_btn.clicked.connect(self._browse_chrome)
        path_row.addWidget(browse_btn)
        layout.addLayout(path_row)

        # 자동 감지된 경로 표시
        detected = detect_chrome_paths()
        if detected:
            hint = QLabel("자동 감지된 경로:")
            hint.setStyleSheet(f"color: {Colors.TEXT_LIGHT}; font-size: 11px; margin-top: 4px;")
            layout.addWidget(hint)
            for path in detected:
                path_btn = AppButton(path, "text")
                path_btn.setStyleSheet(StyleSheet.path_suggestion_button())
                path_btn.setCursor(Qt.PointingHandCursor)
                path_btn.clicked.connect(lambda checked, p=path: self._chrome_path_edit.setText(p))
                layout.addWidget(path_btn)

    def _build_button_section(self, layout: QVBoxLayout):
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = AppButton("취소", "outline")
        cancel_btn.setIcon(AppIcons.icon('cancel'))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = AppButton("저장", "filled")
        save_btn.setIcon(AppIcons.icon('save', color='white'))
        save_btn.clicked.connect(self._save_and_close)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    # ── 헬퍼 ──────────────────────────────────────────────────

    def _make_divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(StyleSheet.divider())
        return line

    def _load_current_settings(self):
        self._prompt_edit.setPlainText(get_summary_prompt())
        self._chrome_path_edit.setText(get_chrome_path())

    def _reset_prompt(self):
        self._prompt_edit.setPlainText(DEFAULT_PROMPT)

    def _browse_chrome(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chrome 실행 파일 선택", "", "모든 파일 (*)"
        )
        if path:
            self._chrome_path_edit.setText(path)

    def _save_and_close(self):
        prompt = self._prompt_edit.toPlainText().strip()
        chrome_path = self._chrome_path_edit.text().strip()

        # 프롬프트 저장 (빈 값이면 기본값 사용)
        set_summary_prompt(prompt if prompt else DEFAULT_PROMPT)

        # Chrome 경로 저장 (경로가 있으면 존재 검증)
        if chrome_path:
            if not os.path.exists(chrome_path):
                QMessageBox.warning(
                    self, "경고",
                    f"지정한 Chrome 경로가 존재하지 않습니다:\n{chrome_path}"
                )
                return
            set_chrome_path(chrome_path)

        self.accept()
