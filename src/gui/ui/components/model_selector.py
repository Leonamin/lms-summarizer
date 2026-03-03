"""
AI 모델 선택 컴포넌트
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLineEdit
from PyQt5.QtCore import Qt

from src.gui.config.constants import Colors
from src.gui.config.styles import StyleSheet


class ModelSelector(QWidget):
    """Gemini AI 모델 선택 위젯 (드롭다운 + 직접 입력)"""

    _MODELS = [
        ("gemini-2.5-flash", "Gemini 2.5 Flash (권장)"),
        ("gemini-2.5-pro", "Gemini 2.5 Pro"),
        ("gemini-2.5-flash-lite", "Gemini 2.5 Flash Lite"),
        ("gemini-2.0-flash", "Gemini 2.0 Flash"),
        ("gemini-2.0-flash-lite", "Gemini 2.0 Flash Lite"),
        ("__custom__", "직접 입력..."),
    ]
    _DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._combo = QComboBox()
        for model_id, display in self._MODELS:
            self._combo.addItem(display, model_id)
        self._combo.setStyleSheet(self._combo_style())
        self._combo.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self._combo)

        self._custom_input = QLineEdit()
        self._custom_input.setPlaceholderText("모델명 직접 입력 (예: gemini-3.0-flash)")
        self._custom_input.setStyleSheet(StyleSheet.input_field())
        self._custom_input.setVisible(False)
        layout.addWidget(self._custom_input)

        self._combo.currentIndexChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self):
        self._custom_input.setVisible(self._combo.currentData() == '__custom__')

    def get_model(self) -> str:
        """선택된 모델명 반환"""
        data = self._combo.currentData()
        if data == '__custom__':
            custom = self._custom_input.text().strip()
            return custom if custom else self._DEFAULT_MODEL
        return data

    def set_model(self, model_name: str):
        """모델명 설정 (저장값 복원)"""
        for i in range(self._combo.count()):
            if self._combo.itemData(i) == model_name:
                self._combo.setCurrentIndex(i)
                return
        # 목록에 없으면 '직접 입력...' 선택 후 텍스트 설정
        for i in range(self._combo.count()):
            if self._combo.itemData(i) == '__custom__':
                self._combo.setCurrentIndex(i)
                self._custom_input.setText(model_name)
                return

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self._combo.setEnabled(enabled)
        self._custom_input.setEnabled(enabled)

    @staticmethod
    def _combo_style() -> str:
        return f"""
            QComboBox {{
                padding: 8px 12px;
                font-size: 13px;
                border: 1.5px solid {Colors.BORDER};
                border-radius: 6px;
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_DARK};
            }}
            QComboBox:focus {{
                border-color: {Colors.BORDER_FOCUS};
            }}
            QComboBox:disabled {{
                background-color: #F5F5F5;
                color: {Colors.TEXT_LIGHT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: {Colors.WHITE};
                selection-background-color: #E3F2FD;
                selection-color: {Colors.TEXT_DARK};
                padding: 4px;
            }}
        """
