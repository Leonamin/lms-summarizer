"""
옵션 섹션 - 동영상 보관 체크박스 + 시작 단계 선택
"""

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.gui.components.stage_selector import StageSelector
from src.gui.core.file_manager import ensure_downloads_directory
from src.pipeline_stage import PipelineStage


class OptionsSection:
    """처리 옵션: 동영상 보관 + 시작 단계 선택"""

    def __init__(self):
        self._save_video_checkbox = ft.Checkbox(
            label="처리 완료 후 원본 동영상 보관",
            value=False,
            active_color=Colors.PRIMARY,
        )

        self.stage_selector = StageSelector()

        self.control = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.TUNE, size=14, color=Colors.TEXT_MUTED),
                        ft.Text(
                            "처리 옵션",
                            size=Typography.CAPTION,
                            weight=Typography.SEMI_BOLD,
                            color=Colors.TEXT_SECONDARY,
                        ),
                    ],
                    spacing=Spacing.XS,
                ),
                self._save_video_checkbox,
                self.stage_selector.control,
            ],
            spacing=Spacing.XS,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

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
