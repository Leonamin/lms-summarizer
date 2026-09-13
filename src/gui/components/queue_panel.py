"""
작업 대기열 패널 — 항목별 상태 표시 + 전체 중지
"""

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.gui.workers.queue_manager import TaskItem, TaskStatus

_STATUS_META = {
    TaskStatus.WAITING: (ft.Icons.SCHEDULE, Colors.TEXT_MUTED, "대기"),
    TaskStatus.DOWNLOADING: (ft.Icons.DOWNLOADING, Colors.PRIMARY, "다운로드 중"),
    TaskStatus.CONVERTING: (ft.Icons.SYNC, Colors.PRIMARY, "WAV 변환 중"),
    TaskStatus.STT: (ft.Icons.GRAPHIC_EQ, Colors.PRIMARY, "텍스트 변환 중"),
    TaskStatus.SUMMARIZING: (ft.Icons.AUTO_AWESOME, Colors.PRIMARY, "요약 생성 중"),
    TaskStatus.DONE: (ft.Icons.CHECK_CIRCLE, "#16A34A", "완료"),
    TaskStatus.FAILED: (ft.Icons.ERROR, Colors.ERROR, "실패"),
    TaskStatus.CANCELLED: (ft.Icons.CANCEL, Colors.WARNING, "취소"),
}


class QueuePanel:
    """작업 대기열 표시 패널 (메인 레이아웃에 삽입, 실행 중 URL 추가 가능)"""

    def __init__(self, on_stop_all=None):
        self._on_stop_all = on_stop_all
        self._rows: dict[int, dict] = {}

        self._summary_text = ft.Text(
            "", size=Typography.SMALL, color=Colors.TEXT_SECONDARY, expand=True,
        )
        self._stop_btn = ft.OutlinedButton(
            content=ft.Text("전체 중지"),
            icon=ft.Icons.STOP_CIRCLE,
            on_click=self._handle_stop_all,
            style=ft.ButtonStyle(
                color=Colors.ERROR,
                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                padding=ft.padding.symmetric(horizontal=12, vertical=4),
                text_style=ft.TextStyle(size=Typography.SMALL, weight=Typography.SEMI_BOLD),
                side=ft.BorderSide(width=1.5, color=Colors.ERROR),
            ),
        )

        self._list = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, height=200)

        self.control = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.PLAYLIST_PLAY, size=16, color=Colors.TEXT_MUTED),
                            ft.Text(
                                "작업 대기열",
                                size=Typography.SMALL,
                                weight=Typography.SEMI_BOLD,
                                color=Colors.TEXT_SECONDARY,
                            ),
                            self._summary_text,
                            self._stop_btn,
                        ],
                        spacing=Spacing.SM,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self._list,
                ],
                spacing=Spacing.XS,
            ),
            bgcolor="#F8FAFC",
            border=ft.border.all(1, Colors.BORDER),
            border_radius=Radius.MD,
            padding=ft.padding.all(Spacing.SM),
            margin=ft.margin.symmetric(horizontal=20),
            visible=False,
        )

    # ── Public API ───────────────────────────────────────

    def update_task(self, task: TaskItem):
        """항목 추가 또는 상태 갱신"""
        row = self._rows.get(task.id)
        if row is None:
            row = self._create_row(task)
            self._rows[task.id] = row
            self._list.controls.append(row["control"])

        icon, color, label = _STATUS_META.get(
            task.status, (ft.Icons.HELP, Colors.TEXT_MUTED, task.status.value))
        row["icon"].name = icon
        row["icon"].color = color
        row["status"].value = label
        row["status"].color = color

        title = task.title or task.url
        if len(title) > 48:
            title = title[:45] + "..."
        row["title"].value = title
        row["title"].tooltip = task.error or task.url

        if task.status == TaskStatus.DOWNLOADING:
            row["icon"].name = ft.Icons.DOWNLOADING  # 회전은 생략, 아이콘으로 구분

        self._update_summary()
        self._safe_update()

    def set_running(self, running: bool):
        """패널 표시/숨김 + 중지 버튼 활성화"""
        self.control.visible = True  # 작업 이력은 유지 표시
        self._stop_btn.disabled = not running
        if not running:
            self._summary_text.value = "대기열 종료"
        self._safe_update()

    def _update_summary(self):
        counts: dict[str, int] = {}
        for row in self._rows.values():
            label = row["status"].value
            counts[label] = counts.get(label, 0) + 1
        parts = [f"{v}개 {k}" for k, v in counts.items()]
        self._summary_text.value = " · ".join(parts) if parts else ""

    def _create_row(self, task: TaskItem) -> dict:
        icon = ft.Icon(ft.Icons.SCHEDULE, size=16, color=Colors.TEXT_MUTED)
        title = ft.Text(
            task.url, size=Typography.SMALL, color=Colors.TEXT,
            expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
        )
        status = ft.Text("대기", size=Typography.SMALL, color=Colors.TEXT_MUTED)
        control = ft.Container(
            content=ft.Row(
                controls=[icon, title, status],
                spacing=Spacing.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=Colors.CARD,
            border_radius=Radius.SM,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
        )
        return {"control": control, "icon": icon, "title": title, "status": status}

    def _handle_stop_all(self, e=None):
        if self._on_stop_all:
            self._on_stop_all()

    def _safe_update(self):
        # main_view에서 invoke_on_ui로 감싸 page.update()를 호출하므로 여기서는 생략
        pass
