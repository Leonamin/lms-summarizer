"""
헤더 컴포넌트 - 앱 제목, 버전, 설정 버튼
"""

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.gui.config.constants import APP_TITLE, APP_VERSION


def build_header(page: ft.Page, on_settings_click=None) -> ft.Container:
    """헤더 UI 구성: 타이틀 + 버전 + 설정 아이콘"""
    # 아이콘을 둥근 박스로 감싸기 (HTML: bg-primary/10 p-1 rounded-lg)
    icon_box = ft.Container(
        content=ft.Icon(ft.Icons.SCHOOL, size=20, color=Colors.PRIMARY),
        bgcolor=ft.Colors.with_opacity(0.1, Colors.PRIMARY),
        border_radius=Radius.MD,
        padding=ft.padding.all(6),
    )

    # 버전 배지 (HTML: bg-slate-100 text-slate-500 rounded px-2)
    version_badge = ft.Container(
        content=ft.Text(
            APP_VERSION,
            size=Typography.SMALL,
            color=Colors.TEXT_MUTED,
        ),
        bgcolor=Colors.SURFACE,
        border_radius=Radius.SM,
        padding=ft.padding.symmetric(horizontal=8, vertical=2),
    )

    return ft.Container(
        content=ft.Row(
            controls=[
                icon_box,
                ft.Text(
                    APP_TITLE,
                    size=Typography.TITLE,
                    weight=Typography.BOLD,
                    color=Colors.TEXT,
                    expand=True,
                ),
                version_badge,
                ft.IconButton(
                    icon=ft.Icons.SETTINGS,
                    icon_color=Colors.ACCENT,
                    icon_size=20,
                    tooltip="설정",
                    on_click=on_settings_click,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
