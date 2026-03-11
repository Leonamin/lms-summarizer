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
            icon=ft.Icons.UPLOAD_FILE,
            on_click=self._handle_pick_files,
            visible=False,
            style=ft.ButtonStyle(
                color=Colors.PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=Radius.MD),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                text_style=ft.TextStyle(size=Typography.CAPTION, weight=Typography.SEMI_BOLD),
                side=ft.BorderSide(width=1, color=ft.Colors.with_opacity(0.3, Colors.PRIMARY)),
            ),
        )

        # 자동 감지 버튼
        self._auto_detect_btn = ft.TextButton(
            content=ft.Text("저장 폴더에서 자동 감지"),
            icon=ft.Icons.SEARCH,
            on_click=self._handle_auto_detect,
            style=ft.ButtonStyle(
                color=Colors.TEXT_SECONDARY,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                text_style=ft.TextStyle(size=Typography.SMALL),
            ),
        )

        # 자동 감지 결과 메시지
        self._detect_info = ft.Text(
            "",
            size=Typography.SMALL,
            color=Colors.INFO,
            visible=False,
        )

        # 선택된 파일 목록 표시 (모두 표시, 외부 스크롤에 위임)
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

        # 모두 제거 버튼
        self._clear_all_btn = ft.TextButton(
            content=ft.Text("모두 제거"),
            icon=ft.Icons.DELETE_SWEEP,
            on_click=self._handle_clear_all,
            visible=False,
            style=ft.ButtonStyle(
                color=Colors.ERROR,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                text_style=ft.TextStyle(size=Typography.SMALL),
            ),
        )

        # 확장자 불일치 경고 메시지
        self._ext_warning = ft.Text(
            "",
            size=Typography.SMALL,
            color=Colors.WARNING,
            visible=False,
        )

        # FilePicker (Flet 0.81+에서는 async 직접 반환)
        self.file_picker = ft.FilePicker()

        self.control = ft.Column(
            controls=[
                self._dropdown,
                ft.Row(
                    controls=[self._pick_btn, self._file_count_text, self._clear_all_btn],
                    spacing=Spacing.SM,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                self._auto_detect_btn,
                self._detect_info,
                self._ext_warning,
                self._file_list,
            ],
            spacing=Spacing.SM,
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
        self._ext_warning.visible = False
        self._ext_warning.value = ""

        if self._pick_btn.page:
            self._pick_btn.page.update()

        if self._on_change:
            self._on_change(stage)

    def _handle_auto_detect(self, e):
        """1단계: 전체 자동 추천 / 2~4단계: 현재 단계에 맞는 파일만 검색"""
        downloads_dir = ensure_downloads_directory()
        current_stage = self.get_stage()

        if current_stage == PipelineStage.DOWNLOAD:
            # 1단계: 전체 자동 추천 (단계까지 변경)
            detector = ArtifactDetector(downloads_dir)
            recommended_stage, files = detector.recommend_start_stage()

            if recommended_stage == PipelineStage.DOWNLOAD and not files:
                self._detect_info.value = "감지된 산출물이 없습니다. 1단계부터 시작합니다."
                self._detect_info.color = Colors.TEXT_MUTED
                self._detect_info.visible = True
            else:
                self.set_stage(recommended_stage)
                self.set_files(files)
                stage_name = STAGE_LABELS[recommended_stage]
                self._detect_info.value = (
                    f"{len(files)}개 파일 감지 → {recommended_stage.value}단계: {stage_name}부터 시작"
                )
                self._detect_info.color = Colors.INFO
                self._detect_info.visible = True
        else:
            # 2~4단계: 현재 단계에 맞는 파일만 검색 (단계 변경 안 함)
            extensions = _STAGE_INPUT_EXTENSIONS.get(current_stage, [])
            found_files = self._scan_for_extensions(downloads_dir, extensions)

            if found_files:
                self.set_files(found_files)
                self._detect_info.value = f"{len(found_files)}개 파일 감지됨"
                self._detect_info.color = Colors.INFO
                self._detect_info.visible = True
            else:
                ext_str = ", ".join(extensions)
                self._detect_info.value = f"저장 폴더에서 {ext_str} 파일을 찾을 수 없습니다."
                self._detect_info.color = Colors.TEXT_MUTED
                self._detect_info.visible = True

        if self._detect_info.page:
            self._detect_info.page.update()

    @staticmethod
    def _scan_for_extensions(directory: str, extensions: list[str]) -> list[str]:
        """디렉토리를 재귀 스캔하여 특정 확장자 파일 목록 반환"""
        import os
        found = []
        if not os.path.isdir(directory):
            return found
        for root, _dirs, files in os.walk(directory):
            for filename in files:
                lower = filename.lower()
                if lower.endswith("_summarized.txt"):
                    continue
                if any(lower.endswith(ext) for ext in extensions):
                    found.append(os.path.join(root, filename))
        return sorted(found)

    def _handle_clear_all(self, e):
        """선택된 파일 모두 제거"""
        self._selected_files.clear()
        self._rebuild_file_list()
        self._ext_warning.visible = False
        self._ext_warning.value = ""
        if self._ext_warning.page:
            self._ext_warning.page.update()

    async def _handle_pick_files(self, e):
        stage = self.get_stage()
        allowed = _STAGE_ALLOWED_EXTENSIONS.get(stage, [])
        file_type = ft.FilePickerFileType.CUSTOM if allowed else ft.FilePickerFileType.ANY
        files = await self.file_picker.pick_files(
            dialog_title="파일 선택",
            allow_multiple=True,
            file_type=file_type,
            allowed_extensions=allowed if allowed else None,
        )
        if not files:
            return

        new_paths = [f.path for f in files if f.path]
        existing = set(self._selected_files)
        added = [p for p in new_paths if p not in existing]

        # 확장자 필터링
        stage = self.get_stage()
        valid_exts = _STAGE_INPUT_EXTENSIONS.get(stage)
        if valid_exts:
            matched = [p for p in added if any(p.lower().endswith(ext) for ext in valid_exts)]
            skipped_count = len(added) - len(matched)
            added = matched

            if skipped_count > 0:
                ext_str = ", ".join(valid_exts)
                self._ext_warning.value = (
                    f"{skipped_count}개 파일이 현재 단계({ext_str})와 맞지 않아 제외됨"
                )
                self._ext_warning.visible = True
            else:
                self._ext_warning.visible = False
                self._ext_warning.value = ""

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
        self._clear_all_btn.visible = has_files

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
        """입력 파일 목록 설정 (확장자 불일치 파일은 필터링)"""
        stage = self.get_stage()
        valid_exts = _STAGE_INPUT_EXTENSIONS.get(stage)

        if valid_exts:
            matched = []
            skipped = []
            for f in files:
                lower = f.lower()
                if any(lower.endswith(ext) for ext in valid_exts):
                    matched.append(f)
                else:
                    skipped.append(f)

            self._selected_files = matched

            if skipped:
                ext_str = ", ".join(valid_exts)
                self._ext_warning.value = (
                    f"{len(skipped)}개 파일이 현재 단계({ext_str})와 맞지 않아 제외됨"
                )
                self._ext_warning.visible = True
            else:
                self._ext_warning.visible = False
                self._ext_warning.value = ""
        else:
            self._selected_files = list(files)
            self._ext_warning.visible = False
            self._ext_warning.value = ""

        self._rebuild_file_list()
