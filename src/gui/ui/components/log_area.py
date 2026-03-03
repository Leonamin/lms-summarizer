"""
로그 영역 컴포넌트
"""

from PyQt5.QtWidgets import QTextEdit, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

from src.gui.config.styles import StyleSheet
from src.gui.config.constants import Limits


class LogArea:
    """로그 영역을 관리하는 클래스"""

    def __init__(self):
        self.label = self._create_label()
        self.text_area = self._create_text_area()

    def _create_label(self) -> QLabel:
        """로그 라벨 생성"""
        label = QLabel("📋 작업 로그:")
        label.setStyleSheet(StyleSheet.label())
        return label

    def _create_text_area(self) -> QTextEdit:
        """로그 텍스트 영역 생성"""
        text_area = QTextEdit()
        text_area.setReadOnly(True)
        text_area.setStyleSheet(StyleSheet.log_area())
        text_area.setMinimumHeight(Limits.LOG_AREA_MIN_HEIGHT)
        text_area.setPlainText("📋 작업 로그가 여기에 표시됩니다...\n")
        return text_area

    def append_message(self, message: str):
        """로그 메시지 추가"""
        self.text_area.append(message)
        self._auto_scroll()

    def clear(self):
        """로그 초기화"""
        self.text_area.clear()
        self.text_area.setPlainText("📋 작업 로그가 여기에 표시됩니다...\n")

    def _auto_scroll(self):
        """자동 스크롤"""
        scrollbar = self.text_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def get_all_text(self) -> str:
        """전체 로그 텍스트 반환"""
        return self.text_area.toPlainText()

    def save_to_file(self, filepath: str):
        """로그를 파일로 저장"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.get_all_text())
            return True
        except Exception as e:
            print(f"로그 저장 실패: {e}")
            return False