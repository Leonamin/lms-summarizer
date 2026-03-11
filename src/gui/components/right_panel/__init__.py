"""
오른쪽 패널 - 강의 선택, 옵션, 액션 바

레이아웃:
- 접힌 상태: 강의 선택(expand) + 옵션 헤더 + 액션 바
- 펼친 상태: 옵션(expand) + 액션 바 (강의 선택 숨김)
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
        self.options = OptionsSection(on_toggle=self._handle_options_toggle)
        self.action_bar = ActionBar(on_start=on_start, on_clear=on_clear)

        self._divider = ft.Divider(height=1, color=Colors.BORDER)

        self.control = ft.Container(
            content=ft.Column(
                controls=[
                    self.lecture.control,
                    self._divider,
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

    def _handle_options_toggle(self, expanded: bool):
        """옵션 펼침/접힘 시 강의 선택 영역 토글"""
        self.lecture.control.visible = not expanded
        self._divider.visible = not expanded
        # 펼침 시 옵션이 남은 공간을 차지
        self.options.control.expand = expanded

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
