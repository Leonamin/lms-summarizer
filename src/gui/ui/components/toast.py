"""
토스트 메시지 컴포넌트 - 잠깐 표시 후 자동으로 사라지는 알림
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer


class ToastMessage(QWidget):
    """잠깐 표시 후 자동으로 사라지는 알림 위젯"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setStyleSheet("""
            ToastMessage {
                background-color: #1E293B;
                border-radius: 8px;
            }
        """)

        self._label = QLabel()
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet(
            "color: #F1F5F9; font-size: 13px; font-weight: 500; background: transparent;"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.addWidget(self._label)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

        self.hide()

    def show_message(self, message: str, duration: int = 2000):
        """토스트 메시지 표시. 이미 표시 중이면 타이머만 리셋."""
        self._label.setText(message)
        self.adjustSize()
        self._reposition()
        self.raise_()
        self.show()
        self._timer.start(duration)

    def reposition(self):
        """부모 위젯 크기 변경 시 위치 재조정"""
        if self.isVisible():
            self._reposition()

    def _reposition(self):
        """부모 위젯 하단 중앙에 위치"""
        parent = self.parentWidget()
        if parent:
            x = (parent.width() - self.width()) // 2
            y = parent.height() - self.height() - 32
            self.move(x, y)
