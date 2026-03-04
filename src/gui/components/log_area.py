"""
Flet 기반 로그 표시 영역
"""

import flet as ft

from src.gui.theme import Colors, Typography, Radius, Spacing


class LogArea:
    """로그 메시지를 표시하는 영역"""

    def __init__(self):
        self._messages: list[str] = []
        self._list_view = ft.ListView(
            spacing=2,
            auto_scroll=True,
            expand=True,
        )
        self.control = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.TERMINAL, size=14, color=Colors.TEXT_MUTED),
                            ft.Text(
                                "로그",
                                size=Typography.CAPTION,
                                weight=Typography.SEMI_BOLD,
                                color=Colors.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=Spacing.XS,
                    ),
                    ft.Container(
                        content=self._list_view,
                        bgcolor=Colors.SURFACE,
                        border_radius=Radius.SM,
                        border=ft.border.all(1, Colors.BORDER),
                        padding=Spacing.SM,
                        expand=True,
                    ),
                ],
                spacing=Spacing.XS,
                expand=True,
            ),
            expand=True,
        )

    def append_message(self, message: str):
        self._messages.append(message)
        self._list_view.controls.append(
            ft.Text(
                message,
                size=Typography.SMALL,
                color=Colors.TEXT_SECONDARY,
                selectable=True,
                no_wrap=False,
            )
        )

    def clear(self):
        self._messages.clear()
        self._list_view.controls.clear()

    def get_all_text(self) -> str:
        return "\n".join(self._messages)
