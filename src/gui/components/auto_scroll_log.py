"""
자동 스크롤 로그 콘솔

새 로그가 생기면 끝으로 자동 스크롤한다. 사용자가 중간을 읽고 있으면
(끝에서 일정 오차 이상 떨어져 있으면) 스크롤하지 않는다.
"""

from datetime import datetime

import flet as ft

from src.gui.theme import Colors, LogDarkColors, Typography, Radius, Spacing

# 끝으로 간주하는 오차 (px) — 이 범위 안이면 자동 스크롤
_BOTTOM_TOLERANCE_PX = 32


class AutoScrollLog:
    """다크 콘솔 스타일의 자동 스크롤 로그"""

    def __init__(self, height: int = 140, expand: bool = False, page=None):
        self._messages: list[str] = []
        self._at_bottom = True  # 마지막 on_scroll 기준 끝 부착 여부
        self._page = page  # scroll_to가 코루틴이라 run_task 실행용

        self._column = ft.Column(
            controls=[],
            scroll=ft.ScrollMode.AUTO,
            spacing=2,
            expand=expand,
            on_scroll=self._handle_scroll,
        )

        self.control = ft.Container(
            content=self._column,
            bgcolor=LogDarkColors.BG,
            border_radius=Radius.MD,
            border=ft.border.all(1, "#374151"),  # slate-700
            padding=ft.padding.all(Spacing.LG),
            height=None if expand else height,
            expand=expand,
        )

    def _handle_scroll(self, e):
        """스크롤 이벤트 — 끝에서 벗어나면 자동 스크롤 중지"""
        pixels = getattr(e, "pixels", None)
        max_extent = getattr(e, "max_scroll_extent", None)
        if pixels is None or max_extent is None:
            return
        self._at_bottom = (max_extent - pixels) <= _BOTTOM_TOLERANCE_PX

    def append_message(self, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{ts}] {message}"
        self._messages.append(formatted)

        self._column.controls.append(
            ft.Text(
                formatted,
                size=Typography.SMALL,
                color=LogDarkColors.TEXT,
                font_family="Courier New, monospace",
                selectable=True,
            )
        )
        if self._at_bottom:
            self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        """끝으로 스크롤 (scroll_to는 코루틴 → page.run_task로 실행)"""
        try:
            coro = self._column.scroll_to(offset=-1, duration=150)
            if self._page is not None:
                self._page.run_task(coro)
        except Exception:
            pass

    def clear(self):
        self._messages.clear()
        self._column.controls.clear()
        self._at_bottom = True

    def get_all_text(self) -> str:
        return "\n".join(self._messages)
