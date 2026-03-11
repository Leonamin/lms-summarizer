"""
다크 테마 로그 드로어 - 하단 접기/펼치기 패널
"""

from datetime import datetime

import flet as ft

from src.gui.theme import Colors, Typography, Radius, Spacing


# 로그 드로어 전용 다크 색상
class LogColors:
    BG = "#1E1E2E"
    SURFACE = "#252535"
    TEXT = "#CDD6F4"
    TEXT_DIM = "#6C7086"
    BORDER = "#313244"
    TIMESTAMP = "#A6E3A1"    # green
    HEADER_BG = "#181825"


class LogDrawer:
    """다크 테마 하단 로그 드로어 (접기/펼치기)"""

    def __init__(self):
        self._messages: list[str] = []
        self._expanded = False

        self._text_field = ft.TextField(
            value="",
            read_only=True,
            multiline=True,
            min_lines=1,
            max_lines=None,
            text_size=Typography.SMALL,
            color=LogColors.TEXT,
            border=ft.InputBorder.NONE,
            content_padding=0,
            expand=True,
            text_style=ft.TextStyle(font_family="Courier New, monospace"),
        )

        self._toggle_icon = ft.Icon(
            ft.Icons.EXPAND_MORE, size=16, color=LogColors.TEXT_DIM,
        )

        self._count_badge = ft.Text(
            "", size=Typography.SMALL, color=LogColors.TEXT_DIM,
        )

        self._log_container = ft.Container(
            content=self._text_field,
            bgcolor=LogColors.BG,
            border_radius=ft.border_radius.only(
                bottom_left=Radius.SM, bottom_right=Radius.SM,
            ),
            padding=Spacing.SM,
            height=140,
            visible=False,
        )

        header_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.TERMINAL, size=14, color=LogColors.TEXT_DIM),
                    ft.Text(
                        "LOG",
                        size=Typography.SMALL,
                        weight=Typography.SEMI_BOLD,
                        color=LogColors.TEXT_DIM,
                    ),
                    self._count_badge,
                    ft.Container(expand=True),
                    self._toggle_icon,
                ],
                spacing=Spacing.XS,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            on_click=self.toggle,
            bgcolor=LogColors.HEADER_BG,
            border_radius=ft.border_radius.only(
                top_left=Radius.SM, top_right=Radius.SM,
            ) if not self._expanded else None,
            padding=ft.padding.symmetric(horizontal=Spacing.SM, vertical=Spacing.XS),
            ink=True,
        )

        self.control = ft.Container(
            content=ft.Column(
                controls=[header_row, self._log_container],
                spacing=0,
            ),
            border=ft.border.all(1, LogColors.BORDER),
            border_radius=Radius.SM,
        )

    def toggle(self, e=None):
        self._expanded = not self._expanded
        self._log_container.visible = self._expanded
        self._toggle_icon.name = (
            ft.Icons.EXPAND_LESS if self._expanded else ft.Icons.EXPAND_MORE
        )
        try:
            self.control.update()
        except Exception:
            pass

    def append_message(self, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{ts}] {message}"
        self._messages.append(formatted)

        if self._text_field.value:
            self._text_field.value += "\n" + formatted
        else:
            self._text_field.value = formatted
        self._count_badge.value = f"({len(self._messages)})"

        # 첫 메시지 시 자동 펼치기
        if not self._expanded:
            self._expanded = True
            self._log_container.visible = True
            self._toggle_icon.name = ft.Icons.EXPAND_LESS

    def clear(self):
        self._messages.clear()
        self._text_field.value = ""
        self._count_badge.value = ""
        self._expanded = False
        self._log_container.visible = False
        self._toggle_icon.name = ft.Icons.EXPAND_MORE

    def get_all_text(self) -> str:
        return "\n".join(self._messages)
