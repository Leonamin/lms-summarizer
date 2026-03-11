"""
액션 바 - 시작/중지 + 초기화 버튼
"""

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius


class ActionBar:
    """하단 액션 바: 요약 시작/중지 + 초기화"""

    def __init__(self, on_start=None, on_clear=None):
        self._on_start = on_start
        self._on_clear = on_clear
        self._is_processing = False

        self._start_btn = ft.ElevatedButton(
            content=ft.Text("요약 시작"),
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._handle_start,
            expand=True,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=Colors.PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=Radius.LG),
                padding=ft.padding.symmetric(vertical=14),
                text_style=ft.TextStyle(weight=Typography.SEMI_BOLD, size=14),
                overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            ),
        )

        self._clear_btn = ft.OutlinedButton(
            content=ft.Text("초기화"),
            icon=ft.Icons.DELETE_OUTLINE,
            on_click=self._handle_clear,
            style=ft.ButtonStyle(
                color=Colors.ERROR,
                shape=ft.RoundedRectangleBorder(radius=Radius.LG),
                padding=ft.padding.symmetric(vertical=14, horizontal=16),
                text_style=ft.TextStyle(weight=Typography.SEMI_BOLD, size=13),
                side=ft.BorderSide(width=2, color=ft.Colors.with_opacity(0.3, Colors.ERROR)),
            ),
        )

        self.control = ft.Container(
            content=ft.Row(
                controls=[self._start_btn, self._clear_btn],
                spacing=Spacing.SM,
            ),
            padding=ft.padding.only(top=4),
        )

    def _handle_start(self, e=None):
        if self._on_start:
            self._on_start()

    def _handle_clear(self, e=None):
        if self._on_clear:
            self._on_clear()

    def set_processing(self, is_processing: bool):
        """처리 중 상태 전환"""
        self._is_processing = is_processing
        if is_processing:
            self._start_btn.content.value = "중지"
            self._start_btn.icon = ft.Icons.STOP
            self._start_btn.style = ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=Colors.ERROR,
                shape=ft.RoundedRectangleBorder(radius=Radius.LG),
                padding=ft.padding.symmetric(vertical=14),
                text_style=ft.TextStyle(weight=Typography.SEMI_BOLD, size=14),
            )
            self._clear_btn.disabled = True
        else:
            self._start_btn.content.value = "요약 시작"
            self._start_btn.icon = ft.Icons.PLAY_ARROW
            self._start_btn.style = ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=Colors.PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=Radius.LG),
                padding=ft.padding.symmetric(vertical=14),
                text_style=ft.TextStyle(weight=Typography.SEMI_BOLD, size=14),
                overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            )
            self._clear_btn.disabled = False

    def set_enabled(self, enabled: bool):
        self._start_btn.disabled = not enabled
        self._clear_btn.disabled = not enabled
