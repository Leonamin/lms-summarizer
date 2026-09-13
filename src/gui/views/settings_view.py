"""
설정 다이얼로그 — 카테고리 내비게이션 구조 (macOS 시스템 설정 스타일)

좌측: 카테고리 목록 (요약 프롬프트 / 브라우저 / 동작)
우측: 선택된 카테고리의 설정 항목
"""

import os
import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius, divider
from src.gui.core.file_manager import (
    get_summary_mode, set_summary_mode,
    get_subject_category, set_subject_category,
    get_subject_custom, set_subject_custom,
    get_chrome_path, set_chrome_path, detect_chrome_paths,
    get_debug_mode, set_debug_mode,
    get_auto_open_folder, set_auto_open_folder,
)
from src.summarize_pipeline.prompts import (
    SummaryMode, SUMMARY_MODE_LABELS, SUBJECT_CATEGORIES,
    build_prompt,
)

# 카테고리 정의: (key, 라벨, 아이콘)
_CATEGORIES = [
    ("summary", "요약 프롬프트", ft.Icons.SUMMARIZE),
    ("browser", "브라우저", ft.Icons.WEB),
    ("behavior", "동작", ft.Icons.TUNE),
]


class SettingsDialog:
    """카테고리 내비게이션형 설정 다이얼로그"""

    def __init__(self, page: ft.Page):
        self._page = page
        self._current = "summary"
        self._cat_buttons: dict[str, ft.Container] = {}
        self._cat_contents: dict[str, ft.Container] = {}

        self._build_summary_tab()
        self._build_browser_tab()
        self._build_behavior_tab()

        self.dialog = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=Radius.LG),
            bgcolor=Colors.BG,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.SETTINGS, size=20, color=Colors.PRIMARY),
                    ft.Text("설정", size=Typography.HEADING,
                            weight=Typography.SEMI_BOLD, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE, icon_size=18,
                        icon_color=Colors.TEXT_MUTED,
                        on_click=self._close, tooltip="닫기",
                    ),
                ],
                spacing=Spacing.SM,
            ),
            content=ft.Container(
                width=640,
                height=460,
                content=ft.Row(
                    controls=[
                        # 좌측 카테고리 목록
                        ft.Container(
                            content=ft.Column(
                                controls=[self._build_category_list()],
                                spacing=0,
                            ),
                            width=180,
                            bgcolor="#F8FAFC",
                            border=ft.border.only(
                                right=ft.BorderSide(1, Colors.BORDER)),
                            border_radius=ft.border_radius.only(
                                top_left=Radius.LG, bottom_left=Radius.LG),
                            padding=ft.padding.all(Spacing.SM),
                        ),
                        # 우측 상세
                        ft.Container(
                            content=ft.Column(
                                controls=list(self._cat_contents.values()),
                                spacing=0,
                            ),
                            expand=True,
                            padding=ft.padding.all(Spacing.LG),
                        ),
                    ],
                    spacing=0,
                ),
            ),
            actions=[
                ft.TextButton(content=ft.Text("취소"), on_click=self._close),
                ft.ElevatedButton(
                    content=ft.Text("저장"),
                    icon=ft.Icons.SAVE,
                    on_click=self._save,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=Colors.PRIMARY,
                        shape=ft.RoundedRectangleBorder(radius=Radius.LG),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    # ── 카테고리 목록 ─────────────────────────────────────

    def _build_category_list(self) -> ft.Column:
        buttons = []
        for key, label, icon in _CATEGORIES:
            btn = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(icon, size=16, color=Colors.TEXT_MUTED),
                        ft.Text(label, size=Typography.BODY,
                                color=Colors.TEXT_MUTED, expand=True),
                    ],
                    spacing=Spacing.SM,
                ),
                padding=ft.padding.symmetric(horizontal=Spacing.SM, vertical=8),
                border_radius=Radius.SM,
                ink=True,
                on_click=lambda e, k=key: self.switch_category(k),
            )
            self._cat_buttons[key] = btn
            buttons.append(btn)
        self._refresh_category_styles()
        return ft.Column(controls=buttons, spacing=2)

    def _refresh_category_styles(self):
        for key, btn in self._cat_buttons.items():
            active = (key == self._current)
            btn.bgcolor = "#EFF6FF" if active else None
            icon = btn.content.controls[0]
            label = btn.content.controls[1]
            icon.color = Colors.PRIMARY if active else Colors.TEXT_MUTED
            label.color = Colors.PRIMARY if active else Colors.TEXT_MUTED
            label.weight = Typography.SEMI_BOLD if active else Typography.REGULAR

    def switch_category(self, key: str):
        if key == self._current:
            return
        self._current = key
        for k, ctrl in self._cat_contents.items():
            ctrl.visible = (k == key)
        self._refresh_category_styles()
        try:
            self.dialog.content.update()
        except Exception:
            self._page.update()

    # ── 요약 프롬프트 탭 ──────────────────────────────────

    def _build_summary_tab(self):
        self.mode_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option(key=k, text=v)
                for k, v in SUMMARY_MODE_LABELS.items()
            ],
            value=get_summary_mode(),
            label="요약 모드",
            border_radius=Radius.MD,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            text_size=Typography.BODY,
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            dense=True,
            on_select=lambda e: self._update_preview(),
        )

        self.subject_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option(key=k, text=k)
                for k in SUBJECT_CATEGORIES.keys()
            ],
            value=get_subject_category(),
            label="강의 분야",
            border_radius=Radius.MD,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            text_size=Typography.BODY,
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            dense=True,
            on_select=lambda e: self._update_preview(),
        )

        self.subject_custom_field = ft.TextField(
            value=get_subject_custom(),
            hint_text="과목명 직접 입력 (선택사항, 드롭다운보다 우선)",
            border_radius=Radius.MD,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            text_size=Typography.BODY,
            label="직접 입력",
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            dense=True,
            on_change=lambda e: self._update_preview(),
        )

        self.prompt_preview = ft.TextField(
            value=build_prompt(
                mode=get_summary_mode(),
                subject_category=get_subject_category(),
                subject_custom=get_subject_custom(),
            ),
            multiline=True,
            min_lines=4,
            max_lines=8,
            border_radius=Radius.MD,
            border_color=Colors.BORDER,
            text_size=Typography.SMALL,
            label="생성된 프롬프트 (미리보기)",
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            read_only=True,
        )

        content = ft.Column(
            controls=[
                ft.Text(
                    "요약 모드와 강의 분야를 선택하면 프롬프트가 자동 생성됩니다.",
                    size=Typography.SMALL, color=Colors.TEXT_MUTED,
                ),
                self.mode_dropdown,
                self.subject_dropdown,
                self.subject_custom_field,
                self.prompt_preview,
                ft.TextButton(
                    content=ft.Text("기본값 복원"),
                    icon=ft.Icons.RESTORE,
                    style=ft.ButtonStyle(
                        color=Colors.ACCENT,
                        text_style=ft.TextStyle(size=Typography.CAPTION),
                    ),
                    on_click=self._reset_prompt,
                ),
            ],
            spacing=Spacing.MD,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        self._cat_contents["summary"] = ft.Container(content=content)

    def _update_preview(self):
        self.prompt_preview.value = build_prompt(
            mode=self.mode_dropdown.value or SummaryMode.NORMAL,
            subject_category=self.subject_dropdown.value or "자동 감지",
            subject_custom=(self.subject_custom_field.value or "").strip(),
        )
        if self.prompt_preview.page:
            self.prompt_preview.update()

    def _reset_prompt(self, e):
        self.mode_dropdown.value = SummaryMode.NORMAL
        self.subject_dropdown.value = "자동 감지"
        self.subject_custom_field.value = ""
        self._update_preview()
        if self.mode_dropdown.page:
            self.mode_dropdown.update()
            self.subject_dropdown.update()
            self.subject_custom_field.update()

    # ── 브라우저 탭 ───────────────────────────────────────

    def _build_browser_tab(self):
        self.chrome_field = ft.TextField(
            value=get_chrome_path(),
            hint_text="Chrome 실행 파일 경로",
            border_radius=Radius.MD,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            text_size=Typography.BODY,
            label="Chrome 경로",
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            prefix_icon=ft.Icons.WEB,
            tooltip="LMS 영상 재생에 사용할 Google Chrome 실행 파일 경로",
        )

        detected_controls = self._build_detected_chrome_controls()

        content = ft.Column(
            controls=[
                ft.Text(
                    "LMS 영상 재생에 사용할 Google Chrome 경로를 설정합니다.",
                    size=Typography.SMALL, color=Colors.TEXT_MUTED,
                ),
                ft.Row(
                    controls=[
                        ft.Container(content=self.chrome_field, expand=True),
                        ft.OutlinedButton(
                            content=ft.Text("찾아보기"),
                            icon=ft.Icons.FOLDER_OPEN,
                            on_click=self._browse_chrome,
                            style=ft.ButtonStyle(
                                color=Colors.PRIMARY,
                                shape=ft.RoundedRectangleBorder(radius=Radius.MD),
                            ),
                        ),
                    ],
                    spacing=Spacing.SM,
                ),
                *detected_controls,
            ],
            spacing=Spacing.MD,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        self._cat_contents["browser"] = ft.Container(content=content)

    def _build_detected_chrome_controls(self) -> list:
        detected_paths = detect_chrome_paths()
        controls = []
        if detected_paths:
            for p in detected_paths:
                controls.append(
                    ft.TextButton(
                        content=ft.Text(f"자동 감지된 경로 사용: {p}", size=Typography.SMALL),
                        style=ft.ButtonStyle(
                            color=Colors.PRIMARY,
                            padding=ft.padding.symmetric(horizontal=4, vertical=2),
                        ),
                        on_click=lambda e, path=p: self._set_chrome_path(path),
                    )
                )
        else:
            controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=16, color="#B45309"),
                                    ft.Text(
                                        "Chrome이 감지되지 않았습니다.",
                                        size=Typography.BODY,
                                        weight=Typography.SEMI_BOLD,
                                        color="#B45309",
                                    ),
                                ],
                                spacing=Spacing.XS,
                            ),
                            ft.Text(
                                "LMS 영상 재생을 위해 Google Chrome이 필요합니다.\n"
                                "아래 버튼으로 Chrome을 다운로드하거나, 이미 설치된 경우 '찾아보기'로 직접 경로를 지정하세요.",
                                size=Typography.SMALL,
                                color="#92400E",
                            ),
                            ft.TextButton(
                                content=ft.Text("Chrome 다운로드 페이지 열기", size=Typography.SMALL),
                                icon=ft.Icons.OPEN_IN_NEW,
                                style=ft.ButtonStyle(
                                    color=Colors.PRIMARY,
                                    padding=ft.padding.symmetric(horizontal=4, vertical=2),
                                ),
                                url="https://www.google.com/chrome/",
                            ),
                        ],
                        spacing=4,
                    ),
                    bgcolor="#FFFBEB",
                    border=ft.border.all(1, "#FDE68A"),
                    border_radius=Radius.MD,
                    padding=ft.padding.all(Spacing.SM),
                )
            )
        return controls

    def _set_chrome_path(self, path):
        self.chrome_field.value = path
        self.chrome_field.update()

    async def _browse_chrome(self, e):
        # FilePicker는 page당 한 번만 overlay에 등록
        if not hasattr(self._page, "_fp_chrome"):
            self._page._fp_chrome = ft.FilePicker()
            self._page.services.append(self._page._fp_chrome)
            self._page.update()
        file_picker = self._page._fp_chrome
        files = await file_picker.pick_files(
            dialog_title="Chrome 실행 파일 선택",
            allowed_extensions=["app", "exe", ""],
        )
        if files:
            self._set_chrome_path(files[0].path)

    # ── 동작 탭 ───────────────────────────────────────────

    def _build_behavior_tab(self):
        self.debug_switch = ft.Switch(
            value=get_debug_mode(),
            active_color=Colors.PRIMARY,
            tooltip="활성화하면 브라우저 창이 표시되어 LMS 동작을 직접 확인할 수 있습니다",
        )
        self.auto_open_switch = ft.Switch(
            value=get_auto_open_folder(),
            active_color=Colors.PRIMARY,
            tooltip="작업 완료 시 결과물이 저장된 폴더를 자동으로 엽니다",
        )

        def _toggle_row(icon, title, desc, switch) -> ft.Container:
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(icon, size=16, color=Colors.TEXT_SECONDARY),
                                        ft.Text(title, size=Typography.BODY,
                                                weight=Typography.SEMI_BOLD,
                                                color=Colors.TEXT),
                                    ],
                                    spacing=Spacing.XS,
                                ),
                                ft.Text(desc, size=Typography.SMALL,
                                        color=Colors.TEXT_MUTED),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        switch,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.symmetric(vertical=Spacing.SM),
            )

        content = ft.Column(
            controls=[
                _toggle_row(
                    ft.Icons.BUG_REPORT, "디버그 모드",
                    "브라우저 창을 표시하여 동작을 확인합니다.",
                    self.debug_switch,
                ),
                divider(),
                _toggle_row(
                    ft.Icons.FOLDER_OPEN, "완료 후 폴더 자동 열기",
                    "작업 완료 시 결과 폴더를 자동으로 엽니다.",
                    self.auto_open_switch,
                ),
            ],
            spacing=Spacing.SM,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        self._cat_contents["behavior"] = ft.Container(content=content)

    # ── 저장/닫기 ─────────────────────────────────────────

    def _close(self, e=None):
        self.dialog.open = False
        self._page.update()

    def _save(self, e):
        chrome_path = (self.chrome_field.value or "").strip()

        set_summary_mode(self.mode_dropdown.value or SummaryMode.NORMAL)
        set_subject_category(self.subject_dropdown.value or "자동 감지")
        set_subject_custom((self.subject_custom_field.value or "").strip())

        set_debug_mode(self.debug_switch.value)
        set_auto_open_folder(self.auto_open_switch.value)

        if chrome_path:
            if not os.path.exists(chrome_path):
                snackbar = ft.SnackBar(
                    content=ft.Text(f"Chrome 경로가 존재하지 않습니다: {chrome_path}"),
                    bgcolor=Colors.ERROR,
                    open=True,
                )
                self._page.overlay.append(snackbar)
                self._page.update()
                return
            set_chrome_path(chrome_path)

        self._close()


def open_settings_dialog(page: ft.Page):
    """설정 다이얼로그를 열고 닫기까지 관리"""
    dialog = SettingsDialog(page)
    page.show_dialog(dialog.dialog)
