"""
옵션 섹션 - 접기/펼치기 가능한 처리 옵션 패널
펼치면 강의 선택 영역을 대체, 접으면 헤더만 표시
"""

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.gui.components.stage_selector import StageSelector
from src.gui.core.file_manager import ensure_downloads_directory
from src.pipeline_stage import PipelineStage


class OptionsSection:
    """처리 옵션: 접기/펼치기 가능한 동영상 보관 + 시작 단계 선택"""

    def __init__(self, on_toggle=None):
        self._on_toggle = on_toggle
        self._expanded = False

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
                    ft.Icon(ft.Icons.TUNE, size=14, color=Colors.TEXT_MUTED),
                    ft.Text(
                        "처리 옵션",
                        size=Typography.CAPTION,
                        weight=Typography.SEMI_BOLD,
                        color=Colors.TEXT_SECONDARY,
                        expand=True,
                    ),
                    self._chevron,
                ],
                spacing=Spacing.XS,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            on_click=self._handle_toggle,
            padding=ft.padding.symmetric(vertical=4, horizontal=2),
            border_radius=Radius.SM,
            ink=True,
        )

        # 옵션 본문 (접혀있을 때 숨김)
        self._body = ft.Column(
            controls=[
                self._save_video_checkbox,
                self.stage_selector.control,
            ],
            spacing=Spacing.XS,
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

    def set_enabled(self, enabled: bool):
        self._save_video_checkbox.disabled = not enabled
        self.stage_selector.set_enabled(enabled)
