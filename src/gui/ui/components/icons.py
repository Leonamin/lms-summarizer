"""
Material Design Icons 제공 모듈 (qtawesome 기반)

사용법:
    from src.gui.ui.components.icons import AppIcons

    # 버튼에 아이콘 추가
    button.setIcon(AppIcons.icon('settings'))

    # 아이콘 + 텍스트 복합 라벨 생성
    label = AppIcons.label('folder', '저장 경로:')
"""

import qtawesome as qta
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import QSize, Qt

from src.gui.config.constants import Colors


# 아이콘 이름 매핑 (앱 내부 → Material Design Icons 6)
_ICON_MAP = {
    # 버튼
    'start': 'mdi6.play',
    'stop': 'mdi6.stop',
    'delete': 'mdi6.delete',
    'settings': 'mdi6.cog',
    'folder_open': 'mdi6.folder-open',
    'save': 'mdi6.content-save',
    'cancel': 'mdi6.close',
    'reset': 'mdi6.restore',
    'browse': 'mdi6.folder-search',

    # 비밀번호 토글
    'visibility': 'mdi6.eye-outline',
    'visibility_off': 'mdi6.eye-off-outline',

    # 입력 필드 라벨
    'school': 'mdi6.school',
    'lock': 'mdi6.lock',
    'key': 'mdi6.key-variant',
    'movie': 'mdi6.movie-open',

    # 섹션 헤더
    'graduation': 'mdi6.school',
    'book': 'mdi6.book-open-variant',
    'folder': 'mdi6.folder',
    'robot': 'mdi6.robot',
    'video': 'mdi6.video',
    'log': 'mdi6.clipboard-text-outline',
    'prompt': 'mdi6.text-box-edit-outline',
    'chrome': 'mdi6.google-chrome',

    # 진행 상태
    'check_circle': 'mdi6.check-circle',
    'circle_outline': 'mdi6.circle-outline',
    'record_circle': 'mdi6.record-circle',
    'chevron_down': 'mdi6.chevron-down',
    'chevron_up': 'mdi6.chevron-up',

    # 강의 목록
    'refresh': 'mdi6.refresh',
    'back': 'mdi6.arrow-left',
    'select_all': 'mdi6.checkbox-multiple-marked',
    'deselect_all': 'mdi6.checkbox-multiple-blank-outline',
    'star': 'mdi6.star',
    'star_outline': 'mdi6.star-outline',
    'list': 'mdi6.format-list-bulleted',
    'assignment': 'mdi6.clipboard-text',
    'wiki': 'mdi6.note-text',
    'quiz': 'mdi6.help-circle',

    # 기타
    'warning': 'mdi6.alert-outline',
    'processing': 'mdi6.timer-sand',
}

_DEFAULT_COLOR = Colors.TEXT_SECONDARY


class AppIcons:
    """앱 전체에서 사용하는 아이콘 관리 클래스"""

    @staticmethod
    def icon(name: str, color: str = None) -> QIcon:
        """QIcon 반환 (QPushButton.setIcon 등에 사용)"""
        qta_name = _ICON_MAP.get(name, name)
        return qta.icon(qta_name, color=color or _DEFAULT_COLOR)

    @staticmethod
    def pixmap(name: str, size: int = 16, color: str = None) -> QPixmap:
        """QPixmap 반환 (QLabel.setPixmap 등에 사용)"""
        ic = AppIcons.icon(name, color=color)
        return ic.pixmap(QSize(size, size))

    @staticmethod
    def label(icon_name: str, text: str, icon_size: int = 16,
              icon_color: str = None, parent: QWidget = None) -> 'IconLabel':
        """아이콘 + 텍스트 복합 라벨 생성"""
        return IconLabel(icon_name, text, icon_size, icon_color, parent)


class IconLabel(QWidget):
    """아이콘 + 텍스트가 결합된 라벨 위젯"""

    def __init__(self, icon_name: str, text: str, icon_size: int = 16,
                 icon_color: str = None, parent: QWidget = None):
        super().__init__(parent)

        # 투명 배경 - 부모 위젯의 스타일이 투과되어 outline이 생기지 않도록
        super().setStyleSheet("background: transparent; border: none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._icon_label = QLabel()
        self._icon_label.setPixmap(AppIcons.pixmap(icon_name, icon_size, icon_color))
        self._icon_label.setFixedSize(icon_size, icon_size)
        self._icon_label.setAlignment(Qt.AlignCenter)
        self._icon_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self._icon_label, alignment=Qt.AlignVCenter)

        self._text_label = QLabel(text)
        self._text_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self._text_label, alignment=Qt.AlignVCenter)
        layout.addStretch()

    def setStyleSheet(self, style: str):
        """텍스트 라벨에 스타일시트 적용 (배경 투명, margin은 위젯 레벨로 이동)"""
        # margin-top은 위젯 자체에 적용하여 아이콘-텍스트가 정렬되도록
        import re
        margin_match = re.search(r'margin-top:\s*(\d+)px', style)
        if margin_match:
            margin_val = margin_match.group(1)
            super().setStyleSheet(
                f"background: transparent; border: none; margin-top: {margin_val}px;"
            )
            # 텍스트 라벨에서는 margin-top 제거
            cleaned = re.sub(r'margin-top:\s*\d+px;?\s*', '', style)
            self._text_label.setStyleSheet(cleaned + " background: transparent; border: none;")
        else:
            self._text_label.setStyleSheet(style + " background: transparent; border: none;")

    def setAlignment(self, alignment):
        """텍스트 정렬"""
        self._text_label.setAlignment(alignment)

    def setEnabled(self, enabled: bool):
        """활성화 상태 설정"""
        super().setEnabled(enabled)
        self._text_label.setEnabled(enabled)
        self._icon_label.setEnabled(enabled)

    def setVisible(self, visible: bool):
        """표시 상태 설정"""
        super().setVisible(visible)

    def setWordWrap(self, wrap: bool):
        """줄바꿈 설정"""
        self._text_label.setWordWrap(wrap)
