"""
파이프라인 모니터 — 단계별 적체량 표시 (메인 화면 상주, 모달 아님)

  ⬇ 다운로드 [2] ─▶ 🔄 변환 [1] ─▶ 🎙 STT [0] ─▶ 🤖 요약 [3]

클릭하면 해당 단계의 항목 목록을 펼친다.
"""

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.gui.workers.queue_manager import TaskItem, TaskStatus

# 단계별 표시 정의: (라벨, 아이콘, 색상)
_STAGES = [
    ("download", "다운로드", ft.Icons.DOWNLOADING),
    ("convert", "변환", ft.Icons.SYNC),
    ("stt", "STT", ft.Icons.GRAPHIC_EQ),
    ("summary", "요약", ft.Icons.AUTO_AWESOME),
]

_STATUS_TO_STAGE = {
    TaskStatus.DOWNLOADING: "download",
    TaskStatus.CONVERTING: "convert",
    TaskStatus.STT: "stt",
    TaskStatus.SUMMARIZING: "summary",
}

_DONE_COLOR = "#16A34A"
_ERROR_COLOR = Colors.ERROR


class PipelineMonitor:
    """단계별 적체량 인디케이터 + 항목 상세 목록"""

    def __init__(self):
        self._tasks: dict[int, TaskItem] = {}
        self._expanded_stage: str | None = None

        self._stage_cells: dict[str, dict] = {}
        self._detail_column = ft.Column(spacing=4, visible=False)

        row_controls = []
        for i, (key, label, icon) in enumerate(_STAGES):
            if i > 0:
                row_controls.append(ft.Icon(
                    ft.Icons.ARROW_FORWARD, size=14, color=Colors.TEXT_MUTED))
            row_controls.append(self._build_stage_cell(key, label, icon))

        self.control = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "파이프라인",
                                size=Typography.SMALL,
                                weight=Typography.SEMI_BOLD,
                                color=Colors.TEXT_SECONDARY,
                            ),
                            ft.Container(expand=True),
                            self._build_summary_badge(),
                        ],
                        spacing=Spacing.SM,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        controls=row_controls,
                        spacing=Spacing.XS,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    self._detail_column,
                ],
                spacing=Spacing.SM,
            ),
            bgcolor="#F8FAFC",
            border=ft.border.all(1, Colors.BORDER),
            border_radius=Radius.MD,
            padding=ft.padding.all(Spacing.MD),
            margin=ft.margin.symmetric(horizontal=20),
            visible=False,
        )

    def _build_stage_cell(self, key: str, label: str, icon) -> ft.Container:
        count_badge = ft.Text(
            "0", size=Typography.SMALL, weight=Typography.BOLD,
            color=Colors.TEXT_MUTED,
        )
        cell = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icon, size=15, color=Colors.TEXT_MUTED),
                            count_badge,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=4,
                    ),
                    ft.Text(label, size=Typography.CAPTION, color=Colors.TEXT_MUTED),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            border_radius=Radius.SM,
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            ink=True,
            on_click=lambda e, k=key: self._toggle_detail(k),
            tooltip=f"{label} 단계 항목 보기",
        )
        self._stage_cells[key] = {
            "cell": cell, "count": count_badge,
            "icon": cell.content.controls[0].controls[0],
            "label": cell.content.controls[1],
        }
        return cell

    def _build_summary_badge(self) -> ft.Text:
        self._summary = ft.Text("", size=Typography.SMALL, color=Colors.TEXT_MUTED)
        return self._summary

    # ── 업데이트 ─────────────────────────────────────────

    def update_task(self, task: TaskItem):
        """작업 상태 반영"""
        self._tasks[task.id] = task
        self._refresh()
        self.control.visible = True

    def _refresh(self):
        # 단계별 적체량 집계
        counts = {k: 0 for k, _, _ in _STAGES}
        done = failed = 0
        for task in self._tasks.values():
            stage = _STATUS_TO_STAGE.get(task.status)
            if stage:
                counts[stage] += 1
            elif task.status == TaskStatus.DONE:
                done += 1
            elif task.status == TaskStatus.FAILED:
                failed += 1

        for key, _, _ in _STAGES:
            meta = self._stage_cells[key]
            n = counts[key]
            meta["count"].value = str(n)
            active = n > 0
            meta["icon"].color = Colors.PRIMARY if active else Colors.TEXT_MUTED
            meta["label"].color = Colors.PRIMARY if active else Colors.TEXT_MUTED

        parts = []
        if done:
            parts.append(f"완료 {done}")
        if failed:
            parts.append(f"실패 {failed}")
        pending = sum(
            1 for t in self._tasks.values()
            if t.status == TaskStatus.WAITING)
        if pending:
            parts.append(f"대기 {pending}")
        self._summary.value = " · ".join(parts) if parts else ""

        # 상세 목록 갱신
        if self._expanded_stage:
            self._render_detail(self._expanded_stage)

    def _toggle_detail(self, stage: str):
        self._expanded_stage = None if self._expanded_stage == stage else stage
        if self._expanded_stage:
            self._render_detail(stage)
        self._detail_column.visible = self._expanded_stage is not None
        self._safe_update()

    def _render_detail(self, stage: str):
        items = [
            t for t in self._tasks.values()
            if _STATUS_TO_STAGE.get(t.status) == stage
        ]
        # 완료/실패도 최신 순으로 몇 개 표시
        label = dict((k, l) for k, l, _ in _STAGES)[stage]
        controls = [ft.Text(
            f"{label} 단계 — {len(items)}개 항목",
            size=Typography.CAPTION, color=Colors.TEXT_SECONDARY,
        )]
        if not items:
            controls.append(ft.Text(
                "현재 처리 중인 항목이 없습니다.",
                size=Typography.SMALL, color=Colors.TEXT_MUTED,
            ))
        for t in items[:20]:
            title = t.title or t.url
            if len(title) > 44:
                title = title[:41] + "..."
            status_color = Colors.PRIMARY
            if t.status == TaskStatus.FAILED:
                status_color = _ERROR_COLOR
            controls.append(ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PLAY_CIRCLE, size=13, color=status_color),
                    ft.Text(
                        title, size=Typography.SMALL, color=Colors.TEXT,
                        expand=True, max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        tooltip=t.error or t.url,
                    ),
                    ft.Text(
                        t.status.value, size=Typography.CAPTION,
                        color=status_color,
                    ),
                ],
                spacing=Spacing.SM,
            ))
        self._detail_column.controls = controls

    def _safe_update(self):
        try:
            self.control.update()
        except Exception:
            pass
