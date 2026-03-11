"""
Flet 기반 로그 표시 영역 (접기/펼치기 지원)
"""

import flet as ft

from src.gui.theme import Colors, Typography, Radius, Spacing


class LogArea:
    """로그 메시지를 표시하는 영역 (접기/펼치기)"""

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
            color=Colors.TEXT_SECONDARY,
            border=ft.InputBorder.NONE,
            content_padding=0,
            expand=True,
        )

        self._toggle_icon = ft.Icon(
            ft.Icons.EXPAND_MORE, size=16, color=Colors.TEXT_MUTED,
        )

        self._count_badge = ft.Text(
            "", size=Typography.SMALL, color=Colors.TEXT_MUTED,
        )

        self._log_container = ft.Container(
            content=self._text_field,
            bgcolor=Colors.SURFACE,
            border_radius=Radius.SM,
            border=ft.border.all(1, Colors.BORDER),
            padding=Spacing.SM,
            expand=True,
            visible=False,
        )

        header_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.TERMINAL, size=14, color=Colors.TEXT_MUTED),
                    ft.Text(
                        "로그",
                        size=Typography.CAPTION,
                        weight=Typography.SEMI_BOLD,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    self._count_badge,
                    ft.Container(expand=True),
                    self._toggle_icon,
                ],
                spacing=Spacing.XS,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            on_click=self._toggle,
            border_radius=Radius.SM,
            padding=ft.padding.symmetric(horizontal=Spacing.SM, vertical=Spacing.XS),
            ink=True,
        )

        self.control = ft.Column(
            controls=[header_row, self._log_container],
            spacing=Spacing.XS,
            expand=self._expanded,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _toggle(self, e=None):
        self._expanded = not self._expanded
        self._log_container.visible = self._expanded
        self._toggle_icon.icon = (
            ft.Icons.EXPAND_LESS if self._expanded else ft.Icons.EXPAND_MORE
        )
        self.control.expand = self._expanded
        try:
            self.control.update()
        except Exception:
            pass

    def append_message(self, message: str):
        self._messages.append(message)
        if self._text_field.value:
            self._text_field.value += "\n" + message
        else:
            self._text_field.value = message
        self._count_badge.value = f"({len(self._messages)})"

        # 첫 메시지 시 자동 펼치기
        if not self._expanded:
            self._expanded = True
            self._log_container.visible = True
            self._toggle_icon.icon = ft.Icons.EXPAND_LESS
            self.control.expand = True

    def clear(self):
        self._messages.clear()
        self._text_field.value = ""
        self._count_badge.value = ""
        # 초기화 시 접기
        self._expanded = False
        self._log_container.visible = False
        self._toggle_icon.icon = ft.Icons.EXPAND_MORE
        self.control.expand = False

    def get_all_text(self) -> str:
        return "\n".join(self._messages)
