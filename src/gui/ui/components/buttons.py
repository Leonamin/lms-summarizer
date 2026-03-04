"""
버튼 컴포넌트들
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, QSize

from src.gui.config.styles import StyleSheet
from src.gui.ui.components.icons import AppIcons


class AppButton(QPushButton):
    """범용 버튼 컴포넌트 - filled/outline/text/danger 변형 지원"""

    def __init__(self, text: str, variant: str = "filled"):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self._variant = variant
        self.setStyleSheet(StyleSheet.app_button(variant))
        self.setIconSize(QSize(18, 18))

    def set_variant(self, variant: str):
        """버튼 스타일 변형 변경"""
        self._variant = variant
        self.setStyleSheet(StyleSheet.app_button(variant))


class ProcessingButton(AppButton):
    """처리 작업용 버튼 (시작 ↔ 중지 전환)"""

    def __init__(self):
        super().__init__("요약 시작", "filled")
        self.setIcon(AppIcons.icon('start', color='white'))
        self.is_processing = False

    def start_processing(self):
        """처리 시작 → 중지 버튼으로 변경"""
        self.is_processing = True
        self.setText("중지")
        self.setIcon(AppIcons.icon('stop', color='white'))
        self.set_variant("danger")
        self.setEnabled(True)

    def stop_processing(self):
        """처리 완료 → 시작 버튼으로 복원"""
        self.is_processing = False
        self.setText("요약 시작")
        self.setIcon(AppIcons.icon('start', color='white'))
        self.set_variant("filled")
        self.setEnabled(True)

    def set_enabled_with_text(self, enabled: bool, text: str = None):
        """활성화 상태와 텍스트 동시 설정"""
        self.setEnabled(enabled)
        if text:
            self.setText(text)
        elif enabled and not self.is_processing:
            self.setText("요약 시작")
            self.setIcon(AppIcons.icon('start', color='white'))


class ClearButton(AppButton):
    """초기화 버튼"""

    def __init__(self):
        super().__init__("초기화", "danger")
        self.setIcon(AppIcons.icon('delete', color='white'))
        self.setToolTip("모든 입력 필드를 초기화합니다")
