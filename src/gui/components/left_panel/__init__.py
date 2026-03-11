"""
왼쪽 패널 - 계정, AI 설정, 저장 경로
"""

from typing import Dict

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.gui.components.left_panel.account_section import AccountSection
from src.gui.components.left_panel.ai_settings import AISettingsSection
from src.gui.components.left_panel.storage_path import StoragePath


class LeftPanel:
    """왼쪽 패널: 계정 + AI 설정 + 저장 경로"""

    def __init__(self, on_engine_change=None, on_path_changed=None):
        self.account = AccountSection()
        self.ai_settings = AISettingsSection(on_engine_change=on_engine_change)
        self.storage_path = StoragePath(on_path_changed=on_path_changed)

        # 상단 스크롤 영역 (계정 + AI 설정)
        _scrollable_content = ft.Container(
            content=ft.Column(
                controls=[
                    self.account.control,
                    ft.Divider(height=1, color=Colors.BORDER),
                    self.ai_settings.control,
                ],
                spacing=Spacing.LG,
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            expand=True,
            padding=ft.padding.all(Spacing.LG),
        )

        # 하단 고정 영역 (저장 경로 — HTML: border-t bg-slate-50)
        _bottom_pinned = ft.Container(
            content=self.storage_path.control,
            padding=ft.padding.all(Spacing.LG),
            border=ft.border.only(top=ft.BorderSide(1, Colors.BORDER)),
            bgcolor="#F8FAFC",  # slate-50
        )

        self.control = ft.Container(
            content=ft.Column(
                controls=[_scrollable_content, _bottom_pinned],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            width=270,
            bgcolor=Colors.LEFT_PANEL_BG,
        )

    def get_all_inputs(self) -> Dict[str, str]:
        """모든 입력값을 dict로 반환 (worker에 전달용)"""
        values = self.account.get_values()
        values['api_key'] = self.ai_settings.get_api_key()
        return values

    def set_enabled(self, enabled: bool):
        self.account.set_enabled(enabled)
        self.ai_settings.set_enabled(enabled)

    def clear(self):
        self.account.clear()
        self.ai_settings.clear()

    def clear_errors(self):
        self.account.clear_error()

    def load_saved(self, saved: Dict[str, str]):
        """저장된 입력값 복원"""
        self.account.set_values(saved)
        if 'api_key' in saved and saved['api_key']:
            self.ai_settings.set_api_key(saved['api_key'])
        if 'ai_engine' in saved:
            self.ai_settings.set_engine(saved['ai_engine'])
        if 'ai_model' in saved:
            self.ai_settings.set_model(saved['ai_model'])
