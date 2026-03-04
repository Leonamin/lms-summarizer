"""
Flet 기반 입력 필드 컴포넌트
"""

import flet as ft

from src.gui.theme import Colors, Typography, Radius


# 아이콘 이름 → ft.Icons 매핑
_ICON_MAP = {
    "school": ft.Icons.SCHOOL,
    "lock": ft.Icons.LOCK,
    "key": ft.Icons.KEY,
    "movie": ft.Icons.MOVIE,
}


class InputField:
    """입력 필드 래퍼 - TextField 생성 및 관리"""

    def __init__(self, config):
        self.config = config
        icon = _ICON_MAP.get(config.icon)

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

    def get_value(self) -> str:
        return self.control.value or ""

    def set_value(self, value: str):
        self.control.value = value

    def clear(self):
        self.control.value = ""

    def set_enabled(self, enabled: bool):
        self.control.disabled = not enabled
