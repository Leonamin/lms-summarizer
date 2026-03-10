"""
Flet 기반 입력 필드 컴포넌트
"""

import re

import flet as ft

from src.gui.theme import Colors, Typography, Radius, Spacing


# 아이콘 이름 → ft.Icons 매핑
_ICON_MAP = {
    "school": ft.Icons.SCHOOL,
    "lock": ft.Icons.LOCK,
    "key": ft.Icons.KEY,
    "movie": ft.Icons.MOVIE,
}

# 한글 감지 정규식 (자음/모음/완성형)
_KOREAN_RE = re.compile(r'[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f\ua960-\ua97f\ud7b0-\ud7ff]')


class InputField:
    """입력 필드 래퍼 - TextField 생성 및 관리"""

    def __init__(self, config, on_korean_detected=None):
        self.config = config
        self._on_korean_detected = on_korean_detected
        icon = _ICON_MAP.get(config.icon)

        # 한글 경고 텍스트 (비밀번호 전용)
        self._korean_warning = ft.Text(
            "영문 자판으로 전환해주세요",
            size=Typography.SMALL,
            color=Colors.WARNING,
            visible=False,
        )

        if config.is_multiline:
            self.control = ft.TextField(
                label=config.label.rstrip(":"),
                hint_text=config.placeholder,
                multiline=True,
                min_lines=3,
                max_lines=8,
                prefix_icon=icon,
                border_radius=Radius.SM,
                border_color=Colors.BORDER,
                focused_border_color=Colors.PRIMARY,
                cursor_color=Colors.PRIMARY,
                text_size=Typography.BODY,
                label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            )
            self.container = ft.Column(controls=[self.control], spacing=Spacing.XS, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        elif config.is_password:
            self.control = ft.TextField(
                label=config.label.rstrip(":"),
                hint_text=config.placeholder,
                password=True,
                can_reveal_password=True,
                prefix_icon=icon,
                border_radius=Radius.SM,
                border_color=Colors.BORDER,
                focused_border_color=Colors.PRIMARY,
                cursor_color=Colors.PRIMARY,
                text_size=Typography.BODY,
                label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
                on_change=self._check_korean_input,
            )
            self.container = ft.Column(
                controls=[self.control, self._korean_warning],
                spacing=Spacing.XS,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            )
        else:
            self.control = ft.TextField(
                label=config.label.rstrip(":"),
                hint_text=config.placeholder,
                prefix_icon=icon,
                border_radius=Radius.SM,
                border_color=Colors.BORDER,
                focused_border_color=Colors.PRIMARY,
                cursor_color=Colors.PRIMARY,
                text_size=Typography.BODY,
                label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            )
            self.container = ft.Column(controls=[self.control], spacing=Spacing.XS, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def _check_korean_input(self, e):
        """비밀번호 필드에서 한글 입력 감지 → 경고 표시 + 한글 제거"""
        value = e.control.value or ""
        if _KOREAN_RE.search(value):
            # 한글 문자 제거
            cleaned = _KOREAN_RE.sub("", value)
            e.control.value = cleaned
            self._korean_warning.visible = True
            if self._on_korean_detected:
                self._on_korean_detected()
        else:
            self._korean_warning.visible = False
        e.control.update()
        self._korean_warning.update()

    def get_value(self) -> str:
        return self.control.value or ""

    def set_value(self, value: str):
        self.control.value = value

    def clear(self):
        self.control.value = ""
        if self.config.is_password:
            self._korean_warning.visible = False

    def set_enabled(self, enabled: bool):
        self.control.disabled = not enabled
