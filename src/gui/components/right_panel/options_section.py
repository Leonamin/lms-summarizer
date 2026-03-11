"""
옵션 섹션 - 접기/펼치기 가능한 처리 옵션 패널
펼치면 강의 선택 영역을 대체, 접으면 헤더만 표시
"""

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.gui.components.stage_selector import StageSelector
from src.gui.core.file_manager import (
    ensure_downloads_directory,
    get_summary_mode, get_subject_category, get_subject_custom,
)
from src.pipeline_stage import PipelineStage
from src.summarize_pipeline.prompts import (
    SummaryMode, SUMMARY_MODE_LABELS, SUBJECT_CATEGORIES,
)


class OptionsSection:
    """처리 옵션: 접기/펼치기 가능한 동영상 보관 + 시작 단계 선택"""

    def __init__(self, on_toggle=None):
        self._on_toggle = on_toggle
        self._expanded = False

        # ── 요약 모드 드롭다운 ──────────────────────────────
        self._summary_mode_dropdown = ft.Dropdown(
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
        )

        self._summary_mode_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.SUMMARIZE, size=16, color=Colors.TEXT_SECONDARY),
                            ft.Text(
                                "요약 설정",
                                size=Typography.CAPTION,
                                weight=Typography.SEMI_BOLD,
                                color=Colors.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=Spacing.XS,
                    ),
                    self._summary_mode_dropdown,
                ],
                spacing=Spacing.SM,
            ),
            bgcolor="#F8FAFC",
            border_radius=Radius.LG,
            border=ft.border.all(1, Colors.BORDER),
            padding=ft.padding.all(Spacing.MD),
        )

        # ── 강의 분야 드롭다운 + 직접 입력 ─────────────────
        self._subject_category_dropdown = ft.Dropdown(
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
        )

        self._subject_custom_field = ft.TextField(
            value=get_subject_custom(),
            hint_text="과목명 직접 입력 (선택사항, 드롭다운보다 우선)",
            border_radius=Radius.MD,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            text_size=Typography.BODY,
            label="직접 입력",
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            dense=True,
        )

        self._subject_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.SCHOOL, size=16, color=Colors.TEXT_SECONDARY),
                            ft.Text(
                                "강의 분야",
                                size=Typography.CAPTION,
                                weight=Typography.SEMI_BOLD,
                                color=Colors.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=Spacing.XS,
                    ),
                    self._subject_category_dropdown,
                    self._subject_custom_field,
                ],
                spacing=Spacing.SM,
            ),
            bgcolor="#F8FAFC",
            border_radius=Radius.LG,
            border=ft.border.all(1, Colors.BORDER),
            padding=ft.padding.all(Spacing.MD),
        )

        # ── 기존 컨트롤 ────────────────────────────────────
        self._save_video_checkbox = ft.Checkbox(
            label="처리 완료 후 원본 동영상 보관",
            value=False,
            active_color=Colors.PRIMARY,
        )

        self.stage_selector = StageSelector()

        # 펼치기/접기 아이콘
        self._chevron = ft.Icon(
            icon=ft.Icons.EXPAND_LESS,
            size=16,
            color=Colors.TEXT_MUTED,
        )

        # 헤더 바 (클릭으로 토글)
        self._header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "옵션",
                        size=Typography.BODY,
                        weight=Typography.BOLD,
                        color=Colors.TEXT_SECONDARY,
                        expand=True,
                    ),
                    self._chevron,
                ],
                spacing=Spacing.XS,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            on_click=self._handle_toggle,
            padding=ft.padding.symmetric(vertical=6, horizontal=4),
            border_radius=Radius.SM,
            ink=True,
        )

        # 파이프라인 시작 단계 컨테이너
        self._stage_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ALT_ROUTE, size=16, color=Colors.TEXT_SECONDARY),
                            ft.Text(
                                "파이프라인 시작 단계",
                                size=Typography.CAPTION,
                                weight=Typography.SEMI_BOLD,
                                color=Colors.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=Spacing.XS,
                    ),
                    self.stage_selector.control,
                ],
                spacing=Spacing.SM,
            ),
            bgcolor="#F8FAFC",  # slate-50
            border_radius=Radius.LG,
            border=ft.border.all(1, Colors.BORDER),
            padding=ft.padding.all(Spacing.MD),
        )

        # 옵션 본문 (접혀있을 때 숨김)
        self._body = ft.Column(
            controls=[
                self._summary_mode_container,
                self._subject_container,
                self._save_video_checkbox,
                self._stage_container,
            ],
            spacing=Spacing.SM,
            visible=False,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        # 전체 컨트롤
        self.control = ft.Column(
            controls=[
                self._header,
                self._body,
            ],
            spacing=Spacing.XS,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    @property
    def is_expanded(self) -> bool:
        return self._expanded

    def _handle_toggle(self, e=None):
        self._expanded = not self._expanded
        self._body.visible = self._expanded
        self._chevron.icon = ft.Icons.EXPAND_MORE if self._expanded else ft.Icons.EXPAND_LESS

        if self._on_toggle:
            self._on_toggle(self._expanded)

        if self._header.page:
            self._header.page.update()

    def get_save_video(self) -> bool:
        return self._save_video_checkbox.value

    def get_save_video_dir(self) -> str | None:
        """보관 선택 시 다운로드 디렉토리, 미선택 시 None"""
        return ensure_downloads_directory() if self._save_video_checkbox.value else None

    def get_stage(self) -> PipelineStage:
        return self.stage_selector.get_stage()

    def get_files(self) -> list[str]:
        return self.stage_selector.get_files()

    def get_summary_mode(self) -> str:
        return self._summary_mode_dropdown.value or SummaryMode.NORMAL

    def get_subject_category(self) -> str:
        return self._subject_category_dropdown.value or "자동 감지"

    def get_subject_custom(self) -> str:
        return (self._subject_custom_field.value or "").strip()

    def set_enabled(self, enabled: bool):
        self._save_video_checkbox.disabled = not enabled
        self._summary_mode_dropdown.disabled = not enabled
        self._subject_category_dropdown.disabled = not enabled
        self._subject_custom_field.disabled = not enabled
        self.stage_selector.set_enabled(enabled)
