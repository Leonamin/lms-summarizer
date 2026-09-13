"""
로그 드로어 - 하단 접기/펼치기 패널
HTML 디자인: 회색 바 헤더(slate-100) + 펼치면 다크 콘솔 영역
"""

import flet as ft

from src.gui.theme import Colors, Typography, Radius, Spacing
from src.gui.components.auto_scroll_log import AutoScrollLog

# 헤더 바 색상 (회색 계열, HTML: bg-gray-200 / slate-100)
_HEADER_BG = "#E5E7EB"        # gray-200
_HEADER_TEXT = "#6B7280"      # gray-500
_HEADER_BORDER = "#E2E8F0"   # slate-200


class LogDrawer:
    """하단 로그 드로어 — 회색 헤더 바 + 다크 콘솔 (접기/펼치기)"""

    def __init__(self):
        self._expanded = False

        # 자동 스크롤 로그 콘솔 (끝에 있을 때만 새 로그에 맞춰 스크롤)
        self._log = AutoScrollLog(height=140)
        self._messages = self._log._messages  # 하위 호환 (get_all_text 등)

        self._toggle_icon = ft.Icon(
            ft.Icons.EXPAND_MORE, size=16, color=_HEADER_TEXT,
        )

        self._count_badge = ft.Text(
            "", size=Typography.SMALL, color=_HEADER_TEXT,
        )

        # 다크 콘솔 영역 (펼쳤을 때만 보임, HTML: bg-[#1e1e1e] rounded-lg)
        self._log_container = ft.Container(
            content=self._log.control,
            visible=False,
            margin=ft.margin.only(left=Spacing.SM, right=Spacing.SM, bottom=Spacing.SM),
        )

        # 회색 헤더 바 (HTML: bg-slate-100 border-t border-slate-200)
        self._header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.TERMINAL, size=14, color=_HEADER_TEXT),
                    ft.Text(
                        "LOG",
                        size=Typography.SMALL,
                        weight=Typography.SEMI_BOLD,
                        color=_HEADER_TEXT,
                    ),
                    self._count_badge,
                    ft.Container(expand=True),
                    self._toggle_icon,
                ],
                spacing=Spacing.XS,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            on_click=self.toggle,
            bgcolor=_HEADER_BG,
            padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=Spacing.XS),
            ink=True,
        )

        # 전체 컨트롤: 테두리 없음, 라운딩 없음, 하단 밀착
        self.control = ft.Container(
            content=ft.Column(
                controls=[self._header, self._log_container],
                spacing=0,
            ),
            border=ft.border.only(top=ft.BorderSide(1, _HEADER_BORDER)),
        )

    def toggle(self, e=None):
        self._expanded = not self._expanded
        self._log_container.visible = self._expanded
        self._toggle_icon.icon = (
            ft.Icons.EXPAND_LESS if self._expanded else ft.Icons.EXPAND_MORE
        )
        try:
            self.control.update()
        except Exception:
            pass

    def append_message(self, message: str):
        self._log.append_message(message)
        self._count_badge.value = f"({len(self._messages)})"

        # 첫 메시지 시 자동 펼치기
        if not self._expanded:
            self._expanded = True
            self._log_container.visible = True
            self._toggle_icon.icon = ft.Icons.EXPAND_LESS

    def clear(self):
        self._log.clear()
        self._count_badge.value = ""
        self._expanded = False
        self._log_container.visible = False
        self._toggle_icon.icon = ft.Icons.EXPAND_MORE

    def get_all_text(self) -> str:
        return self._log.get_all_text()
