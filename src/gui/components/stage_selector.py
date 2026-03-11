"""
Flet 기반 파이프라인 시작 단계 선택기
"""

import flet as ft

from src.gui.theme import Colors, Typography, Radius, Spacing
from src.pipeline_stage import PipelineStage, STAGE_LABELS


class StageSelector:
    """파이프라인 시작 단계 선택 드롭다운"""

    def __init__(self, on_change=None):
        self._on_change = on_change
        self._selected_files: list[str] = []

        options = [
            ft.dropdown.Option(
                key=str(stage.value),
                text=f"{stage.value}단계: {STAGE_LABELS[stage]}",
            )
            for stage in PipelineStage
        ]

        self._dropdown = ft.Dropdown(
            options=options,
            value=str(PipelineStage.DOWNLOAD.value),
            label="시작 단계",
            leading_icon=ft.Icons.SKIP_NEXT,
            border_radius=Radius.SM,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            text_size=Typography.BODY,
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            on_select=self._handle_change,
            dense=True,
        )

        self.control = ft.Column(
            controls=[self._dropdown],
            spacing=Spacing.XS,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _handle_change(self, e):
        if self._on_change:
            self._on_change(self.get_stage())

    def get_stage(self) -> PipelineStage:
        """현재 선택된 시작 단계 반환"""
        try:
            return PipelineStage(int(self._dropdown.value))
        except (ValueError, TypeError):
            return PipelineStage.DOWNLOAD

    def set_stage(self, stage: PipelineStage):
        """시작 단계 설정"""
        self._dropdown.value = str(stage.value)

    def set_enabled(self, enabled: bool):
        """활성/비활성 설정"""
        self._dropdown.disabled = not enabled

    def get_files(self) -> list[str]:
        """선택된 입력 파일 목록 반환"""
        return list(self._selected_files)

    def set_files(self, files: list[str]):
        """입력 파일 목록 설정"""
        self._selected_files = list(files)
