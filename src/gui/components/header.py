"""
헤더 컴포넌트 - 앱 제목, 버전, 설정 버튼
"""

import flet as ft

from src.gui.theme import Colors, Typography, Spacing
from src.gui.config.constants import APP_TITLE, APP_VERSION


def build_header(page: ft.Page, on_settings_click=None) -> ft.Container:
    """헤더 UI 구성: 타이틀 + 버전 + 설정 아이콘"""
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.SCHOOL, size=22, color=Colors.PRIMARY),
                        ft.Text(
                            APP_TITLE,
                            size=Typography.TITLE,
                            weight=Typography.BOLD,
                            color=Colors.TEXT,
                            expand=True,
                        ),
                        ft.Text(
                            APP_VERSION,
                            size=Typography.SMALL,
                            color=Colors.TEXT_MUTED,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SETTINGS,
                            icon_color=Colors.TEXT_SECONDARY,
                            icon_size=20,
                            tooltip="설정",
                            on_click=on_settings_click,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Text(
                    "숭실대학교 LMS 강의 동영상을 다운로드하고 AI로 요약합니다.",
                    size=Typography.CAPTION,
                    color=Colors.TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
