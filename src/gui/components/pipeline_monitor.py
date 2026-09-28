"""Render public durable-job snapshots; all mutations belong to the service."""
import flet as ft
from src.gui.theme import Colors, Typography, Spacing, Radius

_LABELS = {1: '다운로드', 2: '변환', 3: 'STT', 4: '요약'}
_STATUSES = {'queued': '대기', 'running': '처리 중', 'cancelling': '중지 중',
             'completed': '완료', 'failed': '실패', 'cancelled': '취소', 'interrupted': '중단'}


class PipelineMonitor:
    def __init__(self, on_cancel=None, on_retry=None, on_result=None, on_copy=None):
        self._tasks = {}
        self.on_cancel, self.on_retry = on_cancel, on_retry
        self.on_result, self.on_copy = on_result, on_copy
        self._counts = {stage: ft.Text(size=Typography.SMALL) for stage in _LABELS}
        self._details = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO)
        self.control = ft.Container(
            content=ft.Column([
                ft.Text('파이프라인', size=Typography.SMALL, weight=Typography.SEMI_BOLD),
                ft.Row([ft.Column([ft.Text(label, size=Typography.CAPTION), self._counts[stage]], expand=True)
                        for stage, label in _LABELS.items()]),
                self._details,
            ], spacing=Spacing.SM),
            bgcolor='#F8FAFC', border=ft.border.all(1, Colors.BORDER),
            border_radius=Radius.MD, padding=Spacing.MD,
            margin=ft.margin.symmetric(horizontal=20), visible=False,
        )

    def update_task(self, job):
        previous = self._tasks.get(job['id'])
        if previous and previous['revision'] > job['revision']:
            return
        self._tasks[job['id']] = job
        self.control.visible = True
        counts = {stage: {'queued': 0, 'running': 0} for stage in _LABELS}
        for item in self._tasks.values():
            for run in item['attempts'][-1]['stages']:
                if run['status'] in ('queued', 'running'):
                    counts[run['stage']][run['status']] += 1
        for stage, count in counts.items():
            self._counts[stage].value = f"대기 {count['queued']} · 실행 {count['running']}"
        rows = []
        for item in list(self._tasks.values())[-20:][::-1]:
            status = _STATUSES[item['status']]
            if item['result_kind'] == 'manual_ready':
                status = '프롬프트 준비 완료'
            actions = []
            if item['status'] in ('queued', 'running'):
                actions.append(self._button('취소', self.on_cancel, item))
            if item['retryable']:
                actions.append(self._button('재시도', self.on_retry, item))
            if item['status'] == 'completed':
                actions.append(self._button('결과', self.on_result, item))
                if item['result_kind'] == 'manual_ready':
                    actions.append(self._button('프롬프트 복사', self.on_copy, item))
            error = item['attempts'][-1].get('error_code', '')
            rows.append(ft.Row([
                ft.Text(item['display_name'], size=Typography.SMALL, expand=True,
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, tooltip=error or item['display_name']),
                ft.Text(status, size=Typography.CAPTION,
                        color=Colors.ERROR if item['status'] in ('failed', 'interrupted') else Colors.TEXT_SECONDARY),
                *actions,
            ], spacing=4))
        self._details.controls = rows
        self._details.height = min(108, len(rows) * 36)

    @staticmethod
    def _button(label, callback, job):
        return ft.TextButton(content=ft.Text(label, size=Typography.CAPTION),
                             on_click=lambda e: callback(job) if callback else None)
