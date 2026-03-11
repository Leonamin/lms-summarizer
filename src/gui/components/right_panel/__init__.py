"""
오른쪽 패널 - 강의 선택, 옵션, 액션 바
"""

import flet as ft

from src.gui.theme import Colors, Spacing
from src.gui.components.right_panel.lecture_section import LectureSection
from src.gui.components.right_panel.options_section import OptionsSection
from src.gui.components.right_panel.action_bar import ActionBar
from src.pipeline_stage import PipelineStage


class RightPanel:
    """오른쪽 패널: 강의 선택 + 옵션 + 시작 버튼"""

    def __init__(self, on_start=None, on_clear=None, on_open_course_list=None):
        self.lecture = LectureSection(on_open_course_list=on_open_course_list)
        self.options = OptionsSection()
        self.action_bar = ActionBar(on_start=on_start, on_clear=on_clear)

        self.control = ft.Container(
            content=ft.Column(
                controls=[
                    self.lecture.control,
                    ft.Divider(height=1, color=Colors.BORDER),
                    self.options.control,
                    self.action_bar.control,
                ],
                spacing=Spacing.SM,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            expand=True,
            padding=ft.padding.all(Spacing.MD),
        )

    def get_urls(self) -> str:
        return self.lecture.get_urls()

    def set_urls(self, urls_text: str):
        self.lecture.set_urls(urls_text)

    def get_stage(self) -> PipelineStage:
        return self.options.get_stage()

    def get_files(self) -> list[str]:
        return self.options.get_files()

    def get_save_video_dir(self) -> str | None:
        return self.options.get_save_video_dir()

    def set_processing(self, is_processing: bool):
        self.action_bar.set_processing(is_processing)

    def set_enabled(self, enabled: bool):
        self.lecture.set_enabled(enabled)
        self.options.set_enabled(enabled)
