"""
재사용 가능한 입력 필드 컴포넌트
"""

from PyQt5.QtWidgets import QLabel, QLineEdit, QTextEdit, QPushButton, QHBoxLayout, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QInputMethodEvent

from src.gui.config.settings import InputFieldConfig
from src.gui.config.styles import StyleSheet


class PasswordToggleButton(QPushButton):
    """비밀번호 보이기/숨기기 토글 버튼"""

    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedWidth(38)
        self.setToolTip("비밀번호 표시/숨기기")
        self._update_icon(False)
        self.setStyleSheet(self._style())
        self.toggled.connect(self._update_icon)

    def _update_icon(self, checked: bool):
        self.setText("👁" if not checked else "🙈")

    @staticmethod
    def _style() -> str:
        return """
            QPushButton {
                border: 1.5px solid #D1D5DB;
                border-radius: 6px;
                background-color: white;
                font-size: 15px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #F9FAFB;
                border-color: #9CA3AF;
            }
            QPushButton:checked {
                background-color: #EFF6FF;
                border-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #F5F5F5;
                border-color: #E5E7EB;
                color: #D1D5DB;
            }
        """


class PasswordLineEdit(QWidget):
    """비밀번호 입력 필드 (보이기/숨기기 토글 + Caps Lock 감지)"""

    caps_lock_changed = pyqtSignal(bool)

    def __init__(self, placeholder: str = ""):
        super().__init__()
        self._password_visible = False

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 비밀번호 입력 필드
        self._input = QLineEdit()
        self._input.setPlaceholderText(placeholder)
        self._input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self._input)

        # 보이기/숨기기 토글 버튼
        self._toggle_btn = PasswordToggleButton()
        self._toggle_btn.toggled.connect(self._toggle_visibility)
        layout.addWidget(self._toggle_btn)

        self.setLayout(layout)

        # keyPressEvent: Caps Lock 감지 + 비ASCII 차단
        self._input.keyPressEvent = self._wrapped_key_press
        # inputMethodEvent: 한글 IME 차단
        self._input.inputMethodEvent = self._block_korean_ime
        # textChanged: 붙여넣기 등으로 유입된 비ASCII 제거
        self._input.textChanged.connect(self._filter_non_ascii)

    def _wrapped_key_press(self, event):
        """키 입력 시 Caps Lock 상태 감지 + 비ASCII 차단"""
        text = event.text()
        if text and not text.isascii():
            return  # 한글 등 비ASCII 직접 입력 차단
        QLineEdit.keyPressEvent(self._input, event)
        if text and text.isalpha():
            shift_pressed = bool(event.modifiers() & Qt.ShiftModifier)
            caps_on = (text.isupper() and not shift_pressed) or (text.islower() and shift_pressed)
            self.caps_lock_changed.emit(caps_on)

    def _block_korean_ime(self, event):
        """한글 IME 입력 차단"""
        if event.preeditString():
            QLineEdit.inputMethodEvent(self._input, QInputMethodEvent())
            return
        committed = event.commitString()
        if committed and not committed.isascii():
            return
        QLineEdit.inputMethodEvent(self._input, event)

    def _filter_non_ascii(self, text: str):
        """붙여넣기 등으로 유입된 비ASCII 문자 제거"""
        filtered = ''.join(c for c in text if 32 <= ord(c) <= 126)
        if filtered != text:
            pos = self._input.cursorPosition()
            self._input.blockSignals(True)
            self._input.setText(filtered)
            self._input.blockSignals(False)
            self._input.setCursorPosition(min(pos, len(filtered)))

    def _toggle_visibility(self, checked: bool):
        """비밀번호 보이기/숨기기 전환"""
        self._password_visible = checked
        self._input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    # QLineEdit 호환 인터페이스
    def text(self) -> str:
        return self._input.text()

    def setText(self, text: str):
        self._input.setText(text)

    def clear(self):
        self._input.clear()

    def setFocus(self):
        self._input.setFocus()

    def setStyleSheet(self, style: str):
        self._input.setStyleSheet(style)

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self._input.setEnabled(enabled)
        self._toggle_btn.setEnabled(enabled)


class InputField:
    """입력 필드를 관리하는 클래스"""

    def __init__(self, config: InputFieldConfig):
        self.config = config
        self.label = self._create_label()
        self.widget = self._create_input_widget()
        self.caps_lock_label = None

        if self.config.is_password:
            self._setup_caps_lock_label()

    def _create_label(self) -> QLabel:
        """라벨 생성"""
        label = QLabel(self.config.label)
        label.setStyleSheet(StyleSheet.label())
        return label

    def _create_input_widget(self):
        """입력 위젯 생성"""
        if self.config.is_multiline:
            return self._create_multiline_input()
        else:
            return self._create_single_line_input()

    def _create_single_line_input(self):
        """단일 라인 입력 필드 생성"""
        if self.config.is_password:
            widget = PasswordLineEdit(self.config.placeholder)
        else:
            widget = QLineEdit()
            widget.setPlaceholderText(self.config.placeholder)

        widget.setStyleSheet(StyleSheet.input_field())
        return widget

    def _create_multiline_input(self) -> QTextEdit:
        """멀티라인 입력 필드 생성"""
        widget = QTextEdit()
        widget.setPlaceholderText(self.config.placeholder)
        widget.setStyleSheet(StyleSheet.multiline_input())

        if self.config.max_height:
            widget.setMaximumHeight(self.config.max_height)

        return widget

    def _setup_caps_lock_label(self):
        """Caps Lock 경고 라벨 설정"""
        self.caps_lock_label = QLabel("⚠ Caps Lock이 켜져 있습니다")
        self.caps_lock_label.setStyleSheet(StyleSheet.caps_lock_warning())
        self.caps_lock_label.setVisible(False)
        self.widget.caps_lock_changed.connect(self.caps_lock_label.setVisible)

    def get_value(self) -> str:
        """입력값 반환"""
        if hasattr(self.widget, 'toPlainText'):  # QTextEdit
            return self.widget.toPlainText()
        else:  # QLineEdit or PasswordLineEdit
            return self.widget.text()

    def set_value(self, value: str):
        """입력값 설정"""
        if hasattr(self.widget, 'setPlainText'):  # QTextEdit
            self.widget.setPlainText(value)
        else:  # QLineEdit or PasswordLineEdit
            self.widget.setText(value)

    def clear(self):
        """입력값 초기화"""
        if hasattr(self.widget, 'clear'):
            self.widget.clear()

    def set_enabled(self, enabled: bool):
        """입력 필드 활성화/비활성화"""
        self.widget.setEnabled(enabled)
        self.label.setEnabled(enabled)

    def set_focus(self):
        """포커스 설정"""
        self.widget.setFocus()
