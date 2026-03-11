"""
처리 진행 모달 (Flet AlertDialog)
- 세로 타임라인 스텝퍼
- 진행률 카드
- 다크 콘솔 로그 (항상 표시)
- 완료 화면 (State B)
"""

import time
from datetime import datetime

import flet as ft

from src.gui.theme import Colors, LogDarkColors, Typography, Spacing, Radius, divider
from src.gui.core.file_manager import (
    open_in_file_explorer, ensure_downloads_directory, get_auto_open_folder,
)
from src.pipeline_stage import PipelineStage, STAGE_LABELS

# 처리 단계 정의 (PipelineStage 기반)
_STEPS = [(stage.value, STAGE_LABELS[stage]) for stage in PipelineStage]


class ProgressModal:
    """처리 진행 상황을 표시하는 모달 (타임라인 + 진행률 + 로그)"""

    def __init__(self, page: ft.Page, on_stop=None, start_stage: PipelineStage = PipelineStage.DOWNLOAD):
        self._page = page
        self._on_stop = on_stop
        self._start_stage = start_stage
        self._is_finished = False
        self._log_messages: list[str] = []
        self._last_progress_update: float = 0.0
        self._start_time = time.monotonic()
        self._current_step = start_stage.value
        self._step_timestamps: dict[int, str] = {}

        # ── 타임라인 스텝퍼 ──────────────────────────────
        self._timeline_items: list[dict] = []
        self._timeline_column = ft.Column(spacing=0)

        for num, name in _STEPS:
            if num < start_stage:
                state = "skipped"
            else:
                state = "pending"
            item = {
                "num": num,
                "name": name,
                "state": state,
                "circle": None,
                "line": None,
                "label": None,
                "subtitle": None,
            }
            self._timeline_items.append(item)

        self._build_timeline()

        # ── 진행률 카드 ──────────────────────────────────
        self._progress_pct = ft.Text(
            "0%",
            size=20,
            weight=Typography.BOLD,
            color=Colors.PRIMARY,
        )
        self._progress_desc = ft.Text(
            "작업을 시작하는 중...",
            size=Typography.CAPTION,
            color=Colors.TEXT_SECONDARY,
        )
        self._progress_bar = ft.ProgressBar(
            value=0,
            color=Colors.PRIMARY,
            bgcolor=Colors.PRIMARY_BG,
            bar_height=6,
            border_radius=3,
        )

        progress_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "전체 공정률",
                                size=Typography.CAPTION,
                                color=Colors.TEXT_SECONDARY,
                                expand=True,
                            ),
                            self._progress_pct,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self._progress_desc,
                    self._progress_bar,
                ],
                spacing=Spacing.XS,
            ),
            bgcolor=Colors.SURFACE,
            border_radius=Radius.MD,
            border=ft.border.all(1, Colors.BORDER),
            padding=ft.padding.all(Spacing.MD),
        )

        # ── 다크 콘솔 로그 (항상 표시) ───────────────────
        self._log_field = ft.TextField(
            value="",
            read_only=True,
            multiline=True,
            min_lines=1,
            max_lines=None,
            text_size=Typography.SMALL,
            color=LogDarkColors.TEXT,
            border=ft.InputBorder.NONE,
            content_padding=0,
            expand=True,
            text_style=ft.TextStyle(font_family="Courier New, monospace"),
        )
        self._log_container = ft.Container(
            content=self._log_field,
            bgcolor=LogDarkColors.BG,
            border_radius=Radius.SM,
            border=ft.border.all(1, LogDarkColors.BORDER),
            padding=Spacing.SM,
            height=128,
        )

        # ── 중지 버튼 ───────────────────────────────────
        self._stop_btn = ft.ElevatedButton(
            content=ft.Text("중지"),
            icon=ft.Icons.STOP,
            on_click=self._handle_stop,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=Colors.ERROR,
                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
            ),
        )

        # ── 진행 중 콘텐츠 (State A) ────────────────────
        self._progress_content = ft.Column(
            controls=[
                self._timeline_column,
                progress_card,
                self._log_container,
            ],
            spacing=Spacing.MD,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        # ── 완료 콘텐츠 (State B) ───────────────────────
        self._complete_elapsed = ft.Text("", size=Typography.CAPTION, color=Colors.TEXT_SECONDARY)
        self._complete_path = ft.Text("", size=Typography.CAPTION, color=Colors.TEXT_MUTED)

        self._complete_content = ft.Column(
            controls=[
                ft.Container(height=Spacing.LG),
                # 큰 초록색 체크 아이콘
                ft.Container(
                    content=ft.Icon(ft.Icons.CHECK_CIRCLE, size=64, color=Colors.SUCCESS),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Container(height=Spacing.SM),
                ft.Text(
                    "작업 완료!",
                    size=Typography.TITLE,
                    weight=Typography.BOLD,
                    color=Colors.TEXT,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "결과 파일이 생성되었습니다.",
                    size=Typography.BODY,
                    color=Colors.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=Spacing.MD),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            content=ft.Text("결과 폴더 열기"),
                            icon=ft.Icons.FOLDER_OPEN,
                            on_click=self._handle_open_folder,
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor=Colors.PRIMARY,
                                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                            ),
                        ),
                        ft.OutlinedButton(
                            content=ft.Text("닫기"),
                            on_click=lambda e: self.close(),
                            style=ft.ButtonStyle(
                                color=Colors.TEXT_SECONDARY,
                                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=Spacing.SM,
                ),
                ft.Container(height=Spacing.SM),
                divider(),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self._complete_elapsed,
                            self._complete_path,
                        ],
                        spacing=2,
                    ),
                    padding=ft.padding.symmetric(vertical=Spacing.XS),
                ),
            ],
            spacing=Spacing.XS,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            visible=False,
        )

        # ── 취소 콘텐츠 (State C) ───────────────────────
        self._cancel_elapsed = ft.Text("", size=Typography.CAPTION, color=Colors.TEXT_SECONDARY)

        self._cancel_content = ft.Column(
            controls=[
                ft.Container(height=Spacing.LG),
                ft.Container(
                    content=ft.Icon(ft.Icons.CANCEL, size=64, color=Colors.WARNING),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Container(height=Spacing.SM),
                ft.Text(
                    "작업이 중지되었습니다.",
                    size=Typography.TITLE,
                    weight=Typography.BOLD,
                    color=Colors.TEXT,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=Spacing.MD),
                ft.OutlinedButton(
                    content=ft.Text("닫기"),
                    on_click=lambda e: self.close(),
                    style=ft.ButtonStyle(
                        color=Colors.TEXT_SECONDARY,
                        shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                    ),
                ),
                ft.Container(height=Spacing.SM),
                divider(),
                self._cancel_elapsed,
            ],
            spacing=Spacing.XS,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            visible=False,
        )

        # ── 다이얼로그 타이틀 ────────────────────────────
        self._title_text = ft.Text(
            "작업 진행 중...",
            size=Typography.HEADING,
            weight=Typography.SEMI_BOLD,
            expand=True,
        )

        # ── 다이얼로그 ──────────────────────────────────
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    self._title_text,
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=18,
                        icon_color=Colors.TEXT_MUTED,
                        on_click=self._handle_stop,
                        tooltip="닫기",
                    ),
                ],
            ),
            content=ft.Container(
                width=560,
                content=ft.Column(
                    controls=[
                        self._progress_content,
                        self._complete_content,
                        self._cancel_content,
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
            ),
            actions=[self._stop_btn],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    # ── 타임라인 빌드 ────────────────────────────────────

    def _build_timeline(self):
        """타임라인 컨트롤 생성"""
        self._timeline_column.controls.clear()
        active_items = [item for item in self._timeline_items if item["state"] != "skipped"]

        for idx, item in enumerate(active_items):
            is_last = (idx == len(active_items) - 1)

            # 원형 아이콘
            circle = self._make_circle(item["state"])
            item["circle"] = circle

            # 라벨
            label = ft.Text(
                item["name"],
                size=Typography.BODY,
                weight=Typography.SEMI_BOLD if item["state"] == "active" else Typography.REGULAR,
                color=self._label_color(item["state"]),
            )
            item["label"] = label

            # 부제 (타임스탬프 또는 상태)
            subtitle = ft.Text(
                self._subtitle_text(item),
                size=Typography.SMALL,
                color=Colors.TEXT_MUTED,
            )
            item["subtitle"] = subtitle

            # 연결선
            if not is_last:
                line_color = Colors.PRIMARY if item["state"] in ("completed", "active") else Colors.BORDER
                line = ft.Container(
                    width=2,
                    height=20,
                    bgcolor=line_color,
                    margin=ft.margin.only(left=11),
                )
                item["line"] = line
            else:
                item["line"] = None

            # 행 조립: 원형 + 텍스트
            row = ft.Row(
                controls=[
                    circle,
                    ft.Column(
                        controls=[label, subtitle],
                        spacing=0,
                        expand=True,
                    ),
                ],
                spacing=Spacing.SM,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
            self._timeline_column.controls.append(row)

            # 연결선 행
            if item["line"]:
                self._timeline_column.controls.append(item["line"])

    def _make_circle(self, state: str) -> ft.Container:
        """타임라인 원형 아이콘 생성"""
        size = 24
        if state == "completed":
            return ft.Container(
                content=ft.Icon(ft.Icons.CHECK, size=14, color=ft.Colors.WHITE),
                width=size, height=size,
                border_radius=size // 2,
                bgcolor=Colors.PRIMARY,
                alignment=ft.Alignment.CENTER,
            )
        elif state == "active":
            return ft.Container(
                content=ft.Icon(ft.Icons.SYNC, size=14, color=ft.Colors.WHITE),
                width=size, height=size,
                border_radius=size // 2,
                bgcolor=Colors.PRIMARY,
                alignment=ft.Alignment.CENTER,
            )
        else:  # pending
            return ft.Container(
                width=size, height=size,
                border_radius=size // 2,
                border=ft.border.all(2, Colors.BORDER),
                bgcolor=Colors.CARD,
                alignment=ft.Alignment.CENTER,
            )

    def _label_color(self, state: str) -> str:
        if state == "completed":
            return Colors.PRIMARY
        elif state == "active":
            return Colors.PRIMARY
        return Colors.TEXT_MUTED

    def _subtitle_text(self, item: dict) -> str:
        state = item["state"]
        num = item["num"]
        if state == "completed":
            ts = self._step_timestamps.get(num, "")
            return f"{ts} - 처리 완료" if ts else "처리 완료"
        elif state == "active":
            return "진행 중..."
        return "대기 중"

    def _refresh_timeline(self):
        """타임라인 UI 갱신 (상태 변경 후 호출)"""
        active_items = [item for item in self._timeline_items if item["state"] != "skipped"]

        ctrl_idx = 0
        for idx, item in enumerate(active_items):
            is_last = (idx == len(active_items) - 1)

            # 원형 교체
            new_circle = self._make_circle(item["state"])
            item["circle"] = new_circle
            row = self._timeline_column.controls[ctrl_idx]
            row.controls[0] = new_circle

            # 라벨 업데이트
            item["label"].color = self._label_color(item["state"])
            item["label"].weight = Typography.SEMI_BOLD if item["state"] == "active" else Typography.REGULAR

            # 부제 업데이트
            item["subtitle"].value = self._subtitle_text(item)

            ctrl_idx += 1

            # 연결선 업데이트
            if not is_last:
                line_color = Colors.PRIMARY if item["state"] in ("completed", "active") else Colors.BORDER
                line_ctrl = self._timeline_column.controls[ctrl_idx]
                line_ctrl.bgcolor = line_color
                item["line"] = line_ctrl
                ctrl_idx += 1

    # ── Public API ───────────────────────────────────────

    def show(self):
        self._page.show_dialog(self.dialog)

    def close(self):
        self.dialog.open = False
        self._page.update()

    def update_step(self, step_num: int, step_name: str):
        """현재 단계 업데이트 (step_num: 1-indexed)"""
        self._current_step = step_num
        now_ts = datetime.now().strftime("%H:%M")

        for item in self._timeline_items:
            if item["state"] == "skipped":
                continue
            if item["num"] < step_num:
                if item["state"] != "completed":
                    item["state"] = "completed"
                    if item["num"] not in self._step_timestamps:
                        self._step_timestamps[item["num"]] = now_ts
            elif item["num"] == step_num:
                item["state"] = "active"
            else:
                item["state"] = "pending"

        self._refresh_timeline()
        self._progress_bar.value = 0
        self._progress_pct.value = "0%"
        self._progress_desc.value = f"{step_name} 중..."
        self._safe_update()

    def update_progress(self, current: int, total: int):
        if total > 0:
            pct = current / total
            self._progress_bar.value = pct
            pct_int = int(pct * 100)
            self._progress_pct.value = f"{pct_int}%"
            mb_cur = current / (1024 * 1024)
            mb_tot = total / (1024 * 1024)
            self._progress_desc.value = (
                f"다운로드 중... {pct_int}%  ({mb_cur:.1f} / {mb_tot:.1f} MB)"
            )
            now = time.monotonic()
            if pct >= 1.0 or (now - self._last_progress_update) >= 0.15:
                self._last_progress_update = now
                self._safe_update()

    def append_log(self, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{ts}] {message}"
        self._log_messages.append(formatted)
        if self._log_field.value:
            self._log_field.value += "\n" + formatted
        else:
            self._log_field.value = formatted
        self._safe_update()

    def mark_complete(self):
        self._is_finished = True

        # 타임라인 전체 완료
        now_ts = datetime.now().strftime("%H:%M")
        for item in self._timeline_items:
            if item["state"] == "skipped":
                continue
            item["state"] = "completed"
            if item["num"] not in self._step_timestamps:
                self._step_timestamps[item["num"]] = now_ts

        # State B 전환
        self._progress_content.visible = False
        self._stop_btn.visible = False
        self._title_text.value = ""

        # 소요 시간 계산
        elapsed = time.monotonic() - self._start_time
        elapsed_str = self._format_elapsed(elapsed)
        save_path = ensure_downloads_directory()

        self._complete_elapsed.value = f"총 소요 시간: {elapsed_str}"
        self._complete_path.value = f"저장 위치: {save_path}"
        self._complete_content.visible = True

        if get_auto_open_folder():
            open_in_file_explorer(save_path)

        self._safe_update()

    def mark_cancelled(self):
        self._is_finished = True

        # State C 전환
        self._progress_content.visible = False
        self._stop_btn.visible = False
        self._title_text.value = ""

        elapsed = time.monotonic() - self._start_time
        elapsed_str = self._format_elapsed(elapsed)
        self._cancel_elapsed.value = f"경과 시간: {elapsed_str}"
        self._cancel_content.visible = True

        self._safe_update()

    # ── Private ──────────────────────────────────────────

    def _handle_open_folder(self, e=None):
        open_in_file_explorer(ensure_downloads_directory())

    def _handle_stop(self, e=None):
        if self._is_finished:
            self.close()
            return
        self._stop_btn.disabled = True
        self._stop_btn.content.value = "중지 중..."
        self._page.update()
        if self._on_stop:
            self._on_stop()

    def _format_elapsed(self, seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        if m >= 60:
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def _safe_update(self):
        try:
            # schedule_update: 워커 스레드에서도 안전하게 UI 갱신을 예약
            self._page.schedule_update()
        except Exception:
            pass
