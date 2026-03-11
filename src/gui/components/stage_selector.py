"""
Flet 기반 파이프라인 시작 단계 선택기
"""

from pathlib import Path

import flet as ft

from src.gui.theme import Colors, Typography, Radius, Spacing
from src.gui.core.file_manager import ensure_downloads_directory
from src.gui.core.artifact_detector import ArtifactDetector
from src.pipeline_stage import PipelineStage, STAGE_LABELS

# 각 단계에서 입력으로 받을 파일 확장자
_STAGE_INPUT_EXTENSIONS = {
    PipelineStage.CONVERT_AUDIO: [".mp4", ".ts"],
    PipelineStage.STT: [".wav", ".mp3"],
    PipelineStage.SUMMARIZE: [".txt"],
}

_STAGE_ALLOWED_EXTENSIONS = {
    PipelineStage.CONVERT_AUDIO: ["mp4", "ts"],
    PipelineStage.STT: ["wav", "mp3"],
    PipelineStage.SUMMARIZE: ["txt"],
}


class StageSelector:
    """파이프라인 시작 단계 선택 드롭다운 + 파일 선택기"""

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

        # 파일 선택 버튼
        self._pick_btn = ft.OutlinedButton(
            content=ft.Text("파일 선택"),
            icon=ft.Icons.ATTACH_FILE,
            on_click=self._handle_pick_files,
            visible=False,
            style=ft.ButtonStyle(
                color=Colors.PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                text_style=ft.TextStyle(size=Typography.CAPTION),
            ),
        )

        # 자동 감지 버튼
        self._auto_detect_btn = ft.OutlinedButton(
            content=ft.Text("자동 감지"),
            icon=ft.Icons.SEARCH,
            on_click=self._handle_auto_detect,
            style=ft.ButtonStyle(
                color=Colors.TEXT_SECONDARY,
                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                text_style=ft.TextStyle(size=Typography.CAPTION),
            ),
        )

        # 자동 감지 결과 메시지
        self._detect_info = ft.Text(
            "",
            size=Typography.SMALL,
            color=Colors.INFO,
            visible=False,
        )

        # 선택된 파일 목록 표시
        self._file_list = ft.Column(
            controls=[],
            spacing=2,
            visible=False,
        )

        # 파일 개수 요약 텍스트
        self._file_count_text = ft.Text(
            "",
            size=Typography.CAPTION,
            color=Colors.TEXT_SECONDARY,
            visible=False,
        )

        # FilePicker (page overlay에 등록 필요)
        self.file_picker = ft.FilePicker(on_result=self._on_files_selected)

        self.control = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(content=self._dropdown, expand=True),
                        self._auto_detect_btn,
                    ],
                    spacing=Spacing.SM,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    controls=[self._pick_btn, self._file_count_text],
                    spacing=Spacing.SM,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                self._detect_info,
                self._file_list,
            ],
            spacing=Spacing.XS,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _handle_change(self, e):
        stage = self.get_stage()
        show_picker = stage != PipelineStage.DOWNLOAD
        self._pick_btn.visible = show_picker
        # 단계 변경 시 파일 목록 및 감지 메시지 초기화
        self._selected_files.clear()
        self._file_list.controls.clear()
        self._file_list.visible = False
        self._file_count_text.visible = False
        self._file_count_text.value = ""
        self._detect_info.visible = False
        self._detect_info.value = ""

        if self._pick_btn.page:
            self._pick_btn.page.update()

        if self._on_change:
            self._on_change(stage)

    def _handle_auto_detect(self, e):
        """다운로드 디렉토리를 스캔하여 시작 단계와 파일을 자동 설정"""
        downloads_dir = ensure_downloads_directory()
        detector = ArtifactDetector(downloads_dir)
        recommended_stage, files = detector.recommend_start_stage()

        if recommended_stage == PipelineStage.DOWNLOAD and not files:
            self._detect_info.value = "감지된 산출물이 없습니다. 1단계부터 시작합니다."
            self._detect_info.color = Colors.TEXT_MUTED
            self._detect_info.visible = True
            self.set_stage(PipelineStage.DOWNLOAD)
            self._selected_files.clear()
            self._file_list.controls.clear()
            self._file_list.visible = False
            self._file_count_text.visible = False
            self._pick_btn.visible = False
        else:
            self.set_stage(recommended_stage)
            self.set_files(files)
            stage_name = STAGE_LABELS[recommended_stage]
            self._detect_info.value = (
                f"{len(files)}개 파일 감지 → {recommended_stage.value}단계: {stage_name}부터 시작"
            )
            self._detect_info.color = Colors.INFO
            self._detect_info.visible = True

        if self._detect_info.page:
            self._detect_info.page.update()

    def _handle_pick_files(self, e):
        stage = self.get_stage()
        allowed = _STAGE_ALLOWED_EXTENSIONS.get(stage, [])
        file_type = ft.FilePickerFileType.CUSTOM if allowed else ft.FilePickerFileType.ANY
        self.file_picker.pick_files(
            dialog_title="파일 선택",
            allow_multiple=True,
            file_type=file_type,
            allowed_extensions=allowed if allowed else None,
        )

    def _on_files_selected(self, e: ft.FilePickerResultEvent):
        if not e.files:
            return

        new_paths = [f.path for f in e.files if f.path]
        existing = set(self._selected_files)
        added = [p for p in new_paths if p not in existing]

        self._selected_files.extend(added)
        self._rebuild_file_list()

    def _rebuild_file_list(self):
        """선택된 파일 목록 UI 갱신"""
        self._file_list.controls.clear()

        for filepath in self._selected_files:
            name = Path(filepath).name

            def make_remove(fp=filepath):
                def remove(e):
                    self._selected_files.remove(fp)
                    self._rebuild_file_list()
                return remove

            row = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INSERT_DRIVE_FILE, size=14, color=Colors.TEXT_MUTED),
                    ft.Text(
                        name,
                        size=Typography.SMALL,
                        color=Colors.TEXT_SECONDARY,
                        expand=True,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        tooltip=filepath,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=14,
                        icon_color=Colors.TEXT_MUTED,
                        on_click=make_remove(),
                        tooltip="제거",
                        style=ft.ButtonStyle(
                            padding=ft.padding.all(2),
                        ),
                    ),
                ],
                spacing=Spacing.XS,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
            self._file_list.controls.append(row)

        has_files = len(self._selected_files) > 0
        self._file_list.visible = has_files
        self._file_count_text.visible = has_files
        self._file_count_text.value = f"{len(self._selected_files)}개 파일 선택됨" if has_files else ""

        if self._file_list.page:
            self._file_list.page.update()

    def get_stage(self) -> PipelineStage:
        """현재 선택된 시작 단계 반환"""
        try:
            return PipelineStage(int(self._dropdown.value))
        except (ValueError, TypeError):
            return PipelineStage.DOWNLOAD

    def set_stage(self, stage: PipelineStage):
        """시작 단계 설정"""
        self._dropdown.value = str(stage.value)
        show_picker = stage != PipelineStage.DOWNLOAD
        self._pick_btn.visible = show_picker

    def set_enabled(self, enabled: bool):
        """활성/비활성 설정"""
        self._dropdown.disabled = not enabled
        self._pick_btn.disabled = not enabled
        self._auto_detect_btn.disabled = not enabled

    def get_files(self) -> list[str]:
        """선택된 입력 파일 목록 반환"""
        return list(self._selected_files)

    def set_files(self, files: list[str]):
        """입력 파일 목록 설정"""
        self._selected_files = list(files)
        self._rebuild_file_list()
