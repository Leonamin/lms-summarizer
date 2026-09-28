import asyncio
import unittest
from unittest.mock import AsyncMock
from src.gui.components.auto_scroll_log import AutoScrollLog
from src.gui.components.pipeline_monitor import PipelineMonitor


class DesktopUITests(unittest.TestCase):
    def test_monitor_counts_waiting_and_running_and_ignores_stale_snapshot(self):
        monitor = PipelineMonitor()
        job = {'id': 'job', 'revision': 2, 'status': 'queued', 'display_name': 'lecture.txt',
               'result_kind': '', 'retryable': False, 'attempts': [{'stages': [{'stage': 4, 'status': 'queued'}]}]}
        monitor.update_task(job)
        self.assertEqual(monitor._counts[4].value, '대기 1 · 실행 0')
        running = {**job, 'revision': 3, 'status': 'running',
                   'attempts': [{'stages': [{'stage': 4, 'status': 'running'}]}]}
        monitor.update_task(running)
        monitor.update_task(job)
        self.assertEqual(monitor._counts[4].value, '대기 0 · 실행 1')

    def test_log_scroll_schedules_awaitable_function(self):
        class Page:
            def run_task(self, callback):
                self.callback = callback
        page = Page()
        log = AutoScrollLog(page=page)
        log._column.scroll_to = AsyncMock()
        log.append_message('completed')
        asyncio.run(page.callback())
        log._column.scroll_to.assert_awaited_once_with(offset=-1, duration=150)
