"""
입력 소스 카드 — LMS URL / 로컬 파일 2개 카드, 선택 시 강조
파일 확장자로 파이프라인 시작 단계를 자동 유추한다.
"""

from pathlib import Path

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.core.models.stages import PipelineStage

# 확장자 → 시작 단계 자동 유추
_EXTENSION_STAGE = {
    ".mp4": PipelineStage.CONVERT_AUDIO,
    ".ts": PipelineStage.CONVERT_AUDIO,
    ".wav": PipelineStage.STT,
    ".mp3": PipelineStage.STT,
    ".txt": PipelineStage.SUMMARIZE,
}

# 시작 단계 → 표시 라벨
_STAGE_LABEL = {
    PipelineStage.CONVERT_AUDIO: "변환",
    PipelineStage.STT: "STT",
    PipelineStage.SUMMARIZE: "요약",
}


class SourceCard:
    """입력 소스 선택 카드 (선택 시 강조 테두리)"""

    def __init__(self, key: str, title: str, icon, description: str,
                 on_selected=None):
        self.key = key
        self._on_selected = on_selected
        self._selected = False

        self._icon = ft.Icon(icon, size=28, color=Colors.TEXT_MUTED)
        self._title = ft.Text(
            title, size=Typography.BODY, weight=Typography.SEMI_BOLD,
            color=Colors.TEXT,
        )
        self._desc = ft.Text(
            description, size=Typography.SMALL, color=Colors.TEXT_MUTED,
        )

        self._body = ft.Container(
            content=ft.Column(
                controls=[ft.Row(
                    controls=[self._icon, ft.Column(
                        controls=[self._title, self._desc],
                        spacing=2,
                        expand=True,
                    )],
                    spacing=Spacing.MD,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )],
                spacing=0,
            ),
            expand=True,
            alignment=ft.Alignment.CENTER_LEFT,
        )

        self.control = ft.Container(
            content=self._body,
            border=ft.border.all(2, Colors.BORDER),
            border_radius=Radius.LG,
            bgcolor="#F8FAFC",
            padding=ft.padding.all(Spacing.MD),
            ink=True,
            on_click=self._handle_click,
            expand=True,
        )

    def _handle_click(self, e=None):
        self.set_selected(True)
        if self._on_selected:
            self._on_selected(self.key)

    def set_selected(self, selected: bool):
        self._selected = selected
        self.control.border = ft.border.all(
            2, Colors.PRIMARY if selected else Colors.BORDER)
        self.control.bgcolor = "#EFF6FF" if selected else "#F8FAFC"
        self._icon.color = Colors.PRIMARY if selected else Colors.TEXT_MUTED
        self._title.color = Colors.PRIMARY if selected else Colors.TEXT


class SourceSelector:
    """소스 카드 2개 + 선택된 소스의 입력 영역 관리"""

    def __init__(self, on_source_changed=None):
        self._on_source_changed = on_source_changed
        self._current: str | None = None

        self.lms_card = SourceCard(
            "lms", "LMS 강의", ft.Icons.VIDEO_LIBRARY,
            "강의 URL 입력 또는 목록에서 선택 — 다운로드부터 전체 파이프라인 실행",
            on_selected=self._handle_source,
        )
        self.file_card = SourceCard(
            "file", "로컬 파일", ft.Icons.UPLOAD_FILE,
            "다운로드된 영상/오디오/텍스트 파일 — 확장자에 따라 자동으로 이어서 진행",
            on_selected=self._handle_source,
        )

        self.control = ft.Row(
            controls=[self.lms_card.control, self.file_card.control],
            spacing=Spacing.SM,
        )

    def _handle_source(self, key: str):
        other = self.file_card if key == "lms" else self.lms_card
        other.set_selected(False)
        self._current = key
        if self._on_source_changed:
            self._on_source_changed(key)

    @property
    def current(self) -> str | None:
        return self._current

    def get_stage_for_file(self, path: str) -> PipelineStage:
        """파일 확장자로 해당 파일의 시작 단계를 반환"""
        ext = Path(path).suffix.lower()
        return _EXTENSION_STAGE.get(ext, PipelineStage.CONVERT_AUDIO)

    def get_stage_label_for_file(self, path: str) -> str:
        """파일 확장자로 해당 파일의 시작 단계 라벨(한글)을 반환"""
        return _STAGE_LABEL.get(
            self.get_stage_for_file(path), "변환")
