"""
사이드바 탭 컴포넌트 — 계정/AI/STT/일반 4탭, 한 번에 하나만 표시
"""

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.gui.components.left_panel.account_section import AccountSection
from src.gui.components.left_panel.ai_settings import AISettingsSection
from src.gui.components.left_panel.stt_settings import STTSettingsSection
from src.gui.components.left_panel.storage_path import StoragePath
from src.summarize_pipeline.prompts import (
    SummaryMode, SUMMARY_MODE_LABELS, SUBJECT_CATEGORIES,
)


class Sidebar:
    """좌측 사이드바: 탭으로 설정 그룹 전환 (한 번에 하나만 표시)"""

    TABS = [
        ("account", "계정", ft.Icons.ACCOUNT_CIRCLE),
        ("ai", "AI", ft.Icons.SMART_TOY),
        ("stt", "STT", ft.Icons.MIC),
        ("general", "일반", ft.Icons.TUNE),
    ]

    def __init__(self, page: ft.Page, on_path_changed=None):
        self._page = page
        self._current = "account"

        self.account = AccountSection()
        self.ai_settings = AISettingsSection()
        self.stt_settings = STTSettingsSection(page=page)
        self.storage_path = StoragePath(on_path_changed=on_path_changed)
        self._build_general_tab()

        self._tab_buttons: dict[str, ft.Container] = {}
        self._tab_contents: dict[str, ft.Container] = {}

        self.control = ft.Container(
            content=ft.Column(
                controls=[
                    self._build_tab_bar(),
                    ft.Container(content=self._build_tab_content(), expand=True),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            width=290,
            bgcolor=Colors.LEFT_PANEL_BG,
            padding=ft.padding.only(left=20, right=16),
        )

    # ── 탭 바 ─────────────────────────────────────────────

    def _build_tab_bar(self) -> ft.Container:
        buttons = []
        for key, label, icon in self.TABS:
            btn = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(icon, size=18, color=Colors.TEXT_MUTED),
                        ft.Text(label, size=Typography.CAPTION, color=Colors.TEXT_MUTED),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                ),
                padding=ft.padding.symmetric(vertical=8),
                border_radius=Radius.SM,
                ink=True,
                on_click=lambda e, k=key: self.switch_tab(k),
                expand=True,
                alignment=ft.Alignment.CENTER,
            )
            self._tab_buttons[key] = btn
            buttons.append(btn)

        return ft.Container(
            content=ft.Row(controls=buttons, spacing=2),
            padding=ft.padding.symmetric(vertical=Spacing.SM),
            border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER)),
        )

    def _build_tab_content(self) -> ft.Column:
        contents = {
            "account": ft.Container(
                content=self.account.control,
                padding=ft.padding.symmetric(vertical=Spacing.SM),
            ),
            "ai": ft.Container(
                content=ft.Column(
                    controls=[self.ai_settings.control],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
                padding=ft.padding.symmetric(vertical=Spacing.SM),
            ),
            "stt": ft.Container(
                content=ft.Column(
                    controls=[self.stt_settings.control],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
                padding=ft.padding.symmetric(vertical=Spacing.SM),
            ),
            "general": self._general_tab,
        }
        for key, ctrl in contents.items():
            ctrl.visible = (key == self._current)
            self._tab_contents[key] = ctrl
        return ft.Column(
            controls=list(contents.values()),
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _build_general_tab(self):
        """일반 탭: 저장 경로 + 요약 모드 + 강의 분야 + 원본 보관"""
        from src.gui.core.file_manager import (
            get_summary_mode, get_subject_category, get_subject_custom,
        )

        self._summary_mode_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option(key=k, text=v)
                for k, v in SUMMARY_MODE_LABELS.items()
            ],
            value=get_summary_mode(),
            label="요약 모드",
            border_radius=Radius.SM,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            text_size=Typography.BODY,
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            dense=True,
        )

        self._subject_category_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option(key=k, text=k)
                for k in SUBJECT_CATEGORIES.keys()
            ],
            value=get_subject_category(),
            label="강의 분야",
            border_radius=Radius.SM,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            text_size=Typography.BODY,
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            dense=True,
        )

        self._subject_custom_field = ft.TextField(
            value=get_subject_custom(),
            hint_text="과목명 직접 입력 (선택사항, 우선 적용)",
            border_radius=Radius.SM,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            text_size=Typography.BODY,
            label="직접 입력",
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            dense=True,
        )

        self._save_video_checkbox = ft.Checkbox(
            label="처리 완료 후 원본 동영상 보관",
            value=True,
            active_color=Colors.PRIMARY,
            tooltip="체크 해제 시 요약 완료 후 영상 파일이 자동 삭제됩니다",
        )

        def _section(title: str, icon, controls: list) -> ft.Container:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(icon, size=16, color=Colors.TEXT_SECONDARY),
                                ft.Text(
                                    title, size=Typography.CAPTION,
                                    weight=Typography.SEMI_BOLD,
                                    color=Colors.TEXT_SECONDARY,
                                ),
                            ],
                            spacing=Spacing.XS,
                        ),
                        *controls,
                    ],
                    spacing=Spacing.SM,
                ),
                bgcolor="#F8FAFC",
                border_radius=Radius.LG,
                border=ft.border.all(1, Colors.BORDER),
                padding=ft.padding.all(Spacing.MD),
            )

        self._general_tab = ft.Container(
            content=ft.Column(
                controls=[
                    _section("요약 설정", ft.Icons.SUMMARIZE, [
                        self._summary_mode_dropdown,
                    ]),
                    _section("강의 분야", ft.Icons.SCHOOL, [
                        self._subject_category_dropdown,
                        self._subject_custom_field,
                    ]),
                    _section("파일 처리", ft.Icons.FOLDER, [
                        self._save_video_checkbox,
                    ]),
                    self.storage_path.control,
                ],
                spacing=Spacing.MD,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=ft.padding.symmetric(vertical=Spacing.SM),
        )

    # ── 탭 전환 ───────────────────────────────────────────

    def switch_tab(self, key: str):
        if key == self._current:
            return
        self._current = key
        for k, ctrl in self._tab_contents.items():
            ctrl.visible = (k == key)
        self._refresh_tab_styles()
        try:
            self.control.update()
        except Exception:
            pass

    def _refresh_tab_styles(self):
        for key, btn in self._tab_buttons.items():
            active = (key == self._current)
            label = btn.content.controls[1]
            icon = btn.content.controls[0]
            label.color = Colors.PRIMARY if active else Colors.TEXT_MUTED
            label.weight = Typography.SEMI_BOLD if active else Typography.REGULAR
            icon.color = Colors.PRIMARY if active else Colors.TEXT_MUTED

    # ── Public API (기존 LeftPanel 호환) ──────────────────

    def get_all_inputs(self) -> dict:
        values = self.account.get_values()
        values['api_key'] = self.ai_settings.get_api_key()
        values['base_url'] = self.ai_settings.get_base_url()
        return values

    def get_summary_mode(self) -> str:
        return self._summary_mode_dropdown.value or SummaryMode.NORMAL

    def get_subject_category(self) -> str:
        return self._subject_category_dropdown.value or "자동 감지"

    def get_subject_custom(self) -> str:
        return (self._subject_custom_field.value or "").strip()

    def get_save_video(self) -> bool:
        return self._save_video_checkbox.value

    def set_enabled(self, enabled: bool):
        self.account.set_enabled(enabled)
        self.ai_settings.set_enabled(enabled)
        self.stt_settings.set_enabled(enabled)

    def clear(self):
        self.account.clear()
        self.ai_settings.clear()

    def clear_errors(self):
        self.account.clear_error()

    def load_saved(self, saved: dict):
        self.account.set_values(saved)
        if 'api_key' in saved and saved['api_key']:
            self.ai_settings.set_api_key(saved['api_key'])
        if 'ai_engine' in saved:
            self.ai_settings.set_engine(saved['ai_engine'])
        if 'ai_model' in saved:
            self.ai_settings.set_model(saved['ai_model'])
        if 'base_url' in saved and saved['base_url']:
            self.ai_settings.set_base_url(saved['base_url'])
