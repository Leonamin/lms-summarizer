"""
메인 뷰 (Flet) - 컴포넌트 조합 + 콜백 배선 + 워커 관리
"""

from typing import Dict, List

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.gui.config.constants import Messages
from src.gui.core.validators import InputValidator
from src.gui.core.module_loader import check_required_modules
from src.gui.core.file_manager import (
    ensure_downloads_directory, save_user_inputs, load_user_inputs,
)
from src.gui.components.header import build_header
from src.gui.components.left_panel import LeftPanel
from src.gui.components.right_panel import RightPanel
from src.gui.components.log_drawer import LogDrawer
from src.gui.views.progress_view import ProgressModal
from src.gui.views.settings_view import open_settings_dialog
from src.gui.views.course_list_view import CourseListView
from src.gui.workers.processing_worker import ProcessingWorker
from src.pipeline_stage import PipelineStage


class MainView:
    """메인 뷰 - 컴포넌트 조합 및 비즈니스 로직"""

    def __init__(self, page: ft.Page, modules: Dict, module_errors: List[str]):
        self.page = page
        self.modules = modules
        self.module_errors = module_errors
        self.worker: ProcessingWorker = None
        self.modal: ProgressModal = None
        self._is_processing = False

        # SnackBar
        self._snackbar = ft.SnackBar(content=ft.Text(""), duration=3000)

        # 컴포넌트 생성
        self.left_panel = LeftPanel(
            on_path_changed=lambda p: self.log_drawer.append_message(f"저장 경로 변경: {p}"),
        )
        self.right_panel = RightPanel(
            on_start=self._handle_start,
            on_clear=self._handle_clear,
            on_open_course_list=self._open_course_list,
        )
        self.log_drawer = LogDrawer()

        # UI 빌드
        self._build_ui()
        self._load_saved_inputs()
        self._check_module_status()

    def _build_ui(self):
        """전체 UI 레이아웃 구성"""
        header = build_header(
            self.page,
            on_settings_click=lambda e: open_settings_dialog(self.page),
        )

        self.page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        header,
                        ft.Row(
                            controls=[
                                self.left_panel.control,
                                ft.VerticalDivider(width=1, color=Colors.BORDER),
                                self.right_panel.control,
                            ],
                            expand=True,
                            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                        ),
                        self.log_drawer.control,
                    ],
                    spacing=Spacing.SM,
                    expand=True,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                padding=ft.padding.symmetric(horizontal=20, vertical=16),
                expand=True,
            )
        )

    # ── 이벤트 핸들러 ──────────────────────────────────────

    def _open_course_list(self):
        values = self.left_panel.account.get_values()
        student_id = values.get('student_id', '').strip()
        password = values.get('password', '').strip()

        if not student_id or not password:
            self._show_snackbar("학번과 비밀번호를 먼저 입력해주세요.", Colors.WARNING)
            return

        course_view = CourseListView(
            self.page,
            username=student_id,
            password=password,
            on_urls_selected=self._on_urls_selected,
        )
        course_view.show()

    def _on_urls_selected(self, urls: List[str]):
        current = self.right_panel.get_urls().strip()
        existing = set(line.strip() for line in current.split('\n') if line.strip()) if current else set()

        new_urls = [u for u in urls if u not in existing]
        skipped = len(urls) - len(new_urls)

        if new_urls:
            combined = current + '\n' + '\n'.join(new_urls) if current else '\n'.join(new_urls)
            self.right_panel.set_urls(combined)

        msg = f"강의 목록에서 {len(new_urls)}개 URL이 추가되었습니다."
        if skipped:
            msg += f" (중복 {skipped}개 제외)"
        self.log_drawer.append_message(msg)
        self.right_panel.lecture.update_selected_count(
            len(existing) + len(new_urls)
        )
        self.page.update()

    def _handle_start(self):
        if self._is_processing:
            self._handle_stop()
            return

        self.left_panel.clear_errors()

        engine = self.left_panel.ai_settings.get_engine()
        start_stage = self.right_panel.get_stage()
        inputs = self.left_panel.get_all_inputs()
        inputs['urls'] = self.right_panel.get_urls()

        # 검증
        if start_stage == PipelineStage.DOWNLOAD:
            valid, error_message = InputValidator.validate_all_inputs(
                inputs, skip_api_key=(engine == "clipboard"),
            )
            if not valid:
                self._show_snackbar(error_message, Colors.ERROR)
                return
        else:
            if start_stage <= PipelineStage.SUMMARIZE and engine != "clipboard":
                valid, error = InputValidator.validate_api_key(inputs.get('api_key', ''))
                if not valid:
                    self._show_snackbar(error, Colors.ERROR)
                    return
            input_files = self.right_panel.get_files()
            if not input_files:
                self._show_snackbar("시작 단계에 사용할 파일을 선택해주세요.", Colors.ERROR)
                return

        all_loaded, missing = check_required_modules(self.modules)
        if not all_loaded:
            self._show_snackbar(f"{Messages.MODULE_LOAD_ERROR}: {', '.join(missing)}", Colors.ERROR)
            return

        self._start_processing(inputs)

    def _start_processing(self, inputs: Dict[str, str]):
        engine = self.left_panel.ai_settings.get_engine()
        model_name = self.left_panel.ai_settings.get_model()
        start_stage = self.right_panel.get_stage()
        input_files = self.right_panel.get_files()
        save_user_inputs({**inputs, 'ai_model': model_name, 'ai_engine': engine})

        self._is_processing = True
        self.right_panel.set_processing(True)
        self._set_fields_enabled(False)
        self.log_drawer.clear()

        save_video_dir = self.right_panel.get_save_video_dir()
        self.modal = ProgressModal(self.page, on_stop=self._on_modal_stop, start_stage=start_stage)

        def on_log(msg):
            self.log_drawer.append_message(msg)
            if self.modal:
                self.modal.append_log(msg)
            try:
                self.page.update()
            except Exception:
                pass

        def on_finished(success, message):
            try:
                self._is_processing = False
                self.right_panel.set_processing(False)
                self._set_fields_enabled(True)

                if self.modal:
                    if success:
                        self.modal.mark_complete()
                    else:
                        self.modal.mark_cancelled()

                if success:
                    self._show_snackbar("작업이 완료되었습니다!", Colors.SUCCESS)
                elif message and message.startswith("login_failed:"):
                    parts = message.split(":", 2)
                    reason = parts[1] if len(parts) > 1 else "unknown"
                    display_msg = parts[2] if len(parts) > 2 else message
                    self._show_snackbar(display_msg, Colors.ERROR)
                    if reason == "invalid_credentials":
                        self.left_panel.account.set_error('student_id', "학번을 확인하세요")
                        self.left_panel.account.set_error('password', "비밀번호를 확인하세요")
                    elif reason in ("navigation_timeout", "sso_page_failed"):
                        self.left_panel.account.set_error('student_id', "로그인 서버 연결 실패")
                elif "취소" not in message:
                    self._show_snackbar(f"오류: {message}", Colors.ERROR)
                else:
                    self.page.update()
            except Exception:
                pass
            self.worker = None

        def on_step(step_num, step_name):
            if self.modal:
                self.modal.update_step(step_num, step_name)

        def on_progress(current, total):
            if self.modal:
                self.modal.update_progress(current, total)

        self.worker = ProcessingWorker(
            inputs, self.modules,
            save_video_dir=save_video_dir,
            model_name=model_name,
            engine=engine,
            on_log=on_log,
            on_finished=on_finished,
            on_step_changed=on_step,
            on_progress=on_progress,
            start_stage=start_stage,
            input_files=input_files,
        )

        self.modal.show()
        self.page.update()
        self.worker.start()

    def _handle_stop(self):
        def do_stop(e):
            if self.worker:
                self.worker.request_cancel()
                self.log_drawer.append_message("작업 중지를 요청했습니다...")
            confirm_dialog.open = False
            self.page.update()

        def cancel(e):
            confirm_dialog.open = False
            self.page.update()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("확인"),
            content=ft.Text("진행 중인 작업을 중지하시겠습니까?"),
            actions=[
                ft.TextButton(content=ft.Text("아니오"), on_click=cancel),
                ft.ElevatedButton(content=ft.Text("예"), on_click=do_stop,
                    style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=Colors.ERROR)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(confirm_dialog)

    def _on_modal_stop(self):
        if self.worker:
            self.worker.request_cancel()
            self.log_drawer.append_message("작업 중지를 요청했습니다...")

    def _handle_clear(self):
        def do_clear(e):
            self.left_panel.clear()
            self.right_panel.lecture.clear()
            self.log_drawer.clear()
            confirm_dialog.open = False
            self.page.update()

        def cancel(e):
            confirm_dialog.open = False
            self.page.update()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("확인"),
            content=ft.Text("모든 입력 필드를 초기화하시겠습니까?"),
            actions=[
                ft.TextButton(content=ft.Text("아니오"), on_click=cancel),
                ft.ElevatedButton(content=ft.Text("예"), on_click=do_clear,
                    style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=Colors.ERROR)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(confirm_dialog)

    # ── 유틸리티 ─────────────────────────────────────────────

    def _show_snackbar(self, message: str, bgcolor: str = Colors.PRIMARY):
        try:
            self._snackbar.content.value = message
            self._snackbar.bgcolor = bgcolor
            self._snackbar.open = True
            self.page.show_snack_bar(self._snackbar)
        except Exception:
            pass

    def _set_fields_enabled(self, enabled: bool):
        self.left_panel.set_enabled(enabled)
        self.right_panel.set_enabled(enabled)

    def _check_module_status(self):
        if self.module_errors:
            self.log_drawer.append_message("일부 모듈 로드 실패:")
            for error in self.module_errors:
                self.log_drawer.append_message(f"   - {error}")
            self.log_drawer.append_message(Messages.INSTALL_REQUIREMENTS)
            self.page.update()

    def _load_saved_inputs(self):
        saved = load_user_inputs()
        self.left_panel.load_saved(saved)
        self.page.update()
