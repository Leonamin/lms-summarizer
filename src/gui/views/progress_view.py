"""
처리 진행 모달 (Flet AlertDialog)
"""

import time

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius, divider

# 처리 단계 정의
_STEPS = [
    (1, "영상 다운로드"),
    (2, "음성 → 텍스트 변환"),
    (3, "AI 요약 생성"),
]


class ProgressModal:
    """처리 진행 상황을 표시하는 모달"""

    def __init__(self, page: ft.Page, on_stop=None):
        self._page = page
        self._on_stop = on_stop
        self._is_finished = False
        self._log_visible = False
        self._log_messages: list[str] = []
        self._last_progress_update: float = 0.0

        # 단계 인디케이터
        self._step_rows: list[ft.Row] = []
        for num, name in _STEPS:
            icon = ft.Text("○", size=14, color=Colors.TEXT_MUTED)
            label = ft.Text(
                f"{num}단계: {name}",
                size=Typography.BODY,
                color=Colors.TEXT_MUTED,
            )
            row = ft.Row(controls=[icon, label], spacing=Spacing.SM)
            self._step_rows.append(row)

        # 상태 텍스트
        self._status_text = ft.Text(
            "작업을 시작하는 중...",
            size=Typography.CAPTION,
            color=Colors.TEXT_SECONDARY,
        )

        # 프로그레스 바
        self._progress_bar = ft.ProgressBar(
            value=0,
            color=Colors.PRIMARY,
            bgcolor=Colors.PRIMARY_BG,
            bar_height=6,
            border_radius=3,
        )

        # 로그 영역
        self._log_field = ft.TextField(
            value="",
            read_only=True,
            multiline=True,
            min_lines=1,
            max_lines=None,
            text_size=Typography.SMALL,
            color=Colors.TEXT_SECONDARY,
            border=ft.InputBorder.NONE,
            content_padding=0,
            expand=True,
        )
        self._log_container = ft.Container(
            content=self._log_field,
            bgcolor=Colors.SURFACE,
            border_radius=Radius.SM,
            border=ft.border.all(1, Colors.BORDER),
            padding=Spacing.SM,
            height=120,
            visible=False,
        )

        # 로그 토글 버튼
        self._log_toggle = ft.TextButton(
            content=ft.Text("상세 로그 보기"),
            icon=ft.Icons.EXPAND_MORE,
            style=ft.ButtonStyle(
                color=Colors.PRIMARY,
                text_style=ft.TextStyle(size=Typography.CAPTION),
            ),
            on_click=self._toggle_log,
        )

        # 중지 버튼
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

        # 다이얼로그
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "강의 처리 중...",
                size=Typography.HEADING,
                weight=Typography.SEMI_BOLD,
            ),
            content=ft.Container(
                width=440,
                content=ft.Column(
                    controls=[
                        # 단계 표시
                        ft.Container(
                            content=ft.Column(
                                controls=self._step_rows,
                                spacing=Spacing.XS,
                            ),
                            padding=ft.padding.symmetric(vertical=Spacing.SM),
                        ),
                        divider(),
                        self._status_text,
                        self._progress_bar,
                        self._log_toggle,
                        self._log_container,
                    ],
                    spacing=Spacing.SM,
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
            ),
            actions=[self._stop_btn],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def show(self):
        self._page.show_dialog(self.dialog)

    def close(self):
        self.dialog.open = False
        self._page.update()

    def _toggle_log(self, e=None):
        self._log_visible = not self._log_visible
        self._log_container.visible = self._log_visible
        if self._log_visible:
            self._log_toggle.content.value = "상세 로그 숨기기"
            self._log_toggle.icon = ft.Icons.EXPAND_LESS
        else:
            self._log_toggle.content.value = "상세 로그 보기"
            self._log_toggle.icon = ft.Icons.EXPAND_MORE
        self._page.update()

    def _handle_stop(self, e=None):
        if self._is_finished:
            self.close()
            return
        self._stop_btn.disabled = True
        self._stop_btn.content.value = "중지 중..."
        self._page.update()
        if self._on_stop:
            self._on_stop()

    # ── 외부 업데이트 메서드 (워커 스레드에서 호출) ──

    def update_step(self, step_num: int, step_name: str):
        """현재 단계 업데이트 (step_num: 1-indexed)"""
        for i, (num, name) in enumerate(_STEPS):
            icon_ctrl = self._step_rows[i].controls[0]
            label_ctrl = self._step_rows[i].controls[1]

            if i + 1 < step_num:
                icon_ctrl.value = "✓"
                icon_ctrl.color = Colors.SUCCESS
                label_ctrl.color = Colors.SUCCESS
            elif i + 1 == step_num:
                icon_ctrl.value = "●"
                icon_ctrl.color = Colors.PRIMARY
                icon_ctrl.weight = Typography.BOLD
                label_ctrl.color = Colors.PRIMARY
                label_ctrl.weight = Typography.SEMI_BOLD
            else:
                icon_ctrl.value = "○"
                icon_ctrl.color = Colors.TEXT_MUTED
                label_ctrl.color = Colors.TEXT_MUTED

        self._progress_bar.value = 0
        self._status_text.value = f"{step_name} 중..."
        self._safe_update()

    def update_progress(self, current: int, total: int):
        if total > 0:
            pct = current / total
            self._progress_bar.value = pct
            mb_cur = current / (1024 * 1024)
            mb_tot = total / (1024 * 1024)
            self._status_text.value = (
                f"다운로드 중... {int(pct * 100)}%  ({mb_cur:.1f} / {mb_tot:.1f} MB)"
            )
            now = time.monotonic()
            if pct >= 1.0 or (now - self._last_progress_update) >= 0.15:
                self._last_progress_update = now
                self._safe_update()

    def append_log(self, message: str):
        self._log_messages.append(message)
        if self._log_field.value:
            self._log_field.value += "\n" + message
        else:
            self._log_field.value = message
        self._safe_update()

    def mark_complete(self):
        self._is_finished = True
        for i, (num, name) in enumerate(_STEPS):
            icon_ctrl = self._step_rows[i].controls[0]
            label_ctrl = self._step_rows[i].controls[1]
            icon_ctrl.value = "✓"
            icon_ctrl.color = Colors.SUCCESS
            label_ctrl.color = Colors.SUCCESS

        self._progress_bar.value = 1.0
        self._status_text.value = "모든 작업이 완료되었습니다!"
        self._status_text.color = Colors.SUCCESS
        self._stop_btn.content.value = "닫기"
        self._stop_btn.disabled = False
        self._stop_btn.style = ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=Colors.PRIMARY,
            shape=ft.RoundedRectangleBorder(radius=Radius.SM),
        )
        self._safe_update()

    def mark_cancelled(self):
        self._is_finished = True
        self._stop_btn.content.value = "닫기"
        self._stop_btn.disabled = False
        self._safe_update()

    def _safe_update(self):
        """스레드 안전한 UI 업데이트"""
        try:
            self._page.update()
        except Exception:
            pass
