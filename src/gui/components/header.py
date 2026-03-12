"""
헤더 컴포넌트 - 앱 제목, 버전, 업데이트 확인, 설정 버튼
"""

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.gui.config.constants import APP_TITLE, APP_VERSION
from src.gui.core.thread_safe import invoke_on_ui
from src.gui.core.update_checker import check_for_update


def build_header(page: ft.Page, on_settings_click=None) -> ft.Container:
    """헤더 UI 구성: 타이틀 + 버전 + 업데이트 확인 + 설정 아이콘"""
    # 아이콘을 둥근 박스로 감싸기
    icon_box = ft.Container(
        content=ft.Icon(ft.Icons.SCHOOL, size=20, color=Colors.PRIMARY),
        bgcolor=ft.Colors.with_opacity(0.1, Colors.PRIMARY),
        border_radius=Radius.MD,
        padding=ft.padding.all(6),
    )

    # 버전 배지
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

    # 업데이트 확인 버튼
    update_btn = ft.IconButton(
        icon=ft.Icons.REFRESH,
        icon_color=Colors.TEXT_MUTED,
        icon_size=18,
        tooltip="업데이트 확인",
        style=ft.ButtonStyle(padding=ft.padding.all(4)),
    )

    # 업데이트 확인 결과를 저장할 상태
    _state = {"download_url": None, "has_update": False}

    def _on_update_result(latest_tag, download_url, is_newer):
        _state["download_url"] = download_url
        _state["has_update"] = is_newer
        if is_newer:
            update_btn.icon = ft.Icons.SYSTEM_UPDATE_ALT
            update_btn.icon_color = Colors.SUCCESS
            update_btn.tooltip = f"{latest_tag} 다운로드"
        else:
            update_btn.icon = ft.Icons.CHECK_CIRCLE
            update_btn.icon_color = Colors.TEXT_MUTED
            update_btn.tooltip = "최신 버전입니다"
        update_btn.disabled = False

    def _on_update_click(e):
        if _state["has_update"] and _state["download_url"]:
            page.launch_url(_state["download_url"])
        else:
            # 재확인
            update_btn.disabled = True
            update_btn.icon = ft.Icons.REFRESH
            update_btn.icon_color = Colors.TEXT_MUTED
            update_btn.tooltip = "확인 중..."
            page.update()
            check_for_update(
                APP_VERSION,
                invoke_on_ui(page, _on_update_result),
            )

    update_btn.on_click = _on_update_click

    # 앱 시작 시 자동 확인
    check_for_update(
        APP_VERSION,
        invoke_on_ui(page, _on_update_result),
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
                update_btn,
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
