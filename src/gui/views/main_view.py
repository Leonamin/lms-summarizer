"""
메인 뷰 (Flet) — 백그라운드 큐 중심 레이아웃

구조: 사이드바(탭) | 메인 콘텐츠(소스 카드 + 작업 시작) | 로그 드로어
파이프라인 모니터와 큐 패널은 메인 화면 상주 (모달 없음, 닫아도 작업 유지)
"""

from typing import Dict, List
from pathlib import Path

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.gui.config.constants import Messages
from src.gui.core.validators import InputValidator
from src.gui.core.thread_safe import invoke_on_ui
from src.gui.core.file_manager import (
    ensure_downloads_directory, save_user_inputs, load_user_inputs,
    set_summary_mode, set_subject_category, set_subject_custom,
    get_summary_prompt, get_chrome_path, get_debug_mode,
    get_stt_engine, get_stt_model, get_stt_params,
)
from src.gui.components.header import build_header
from src.gui.components.sidebar import Sidebar
from src.gui.components.source_selector import SourceSelector
from src.gui.components.pipeline_monitor import PipelineMonitor
from src.gui.components.log_drawer import LogDrawer
from src.gui.views.settings_view import open_settings_dialog
from src.gui.views.course_list_view import CourseListView


class MainView:
    """메인 뷰 — 큐 중심 재구성"""

    def __init__(self, page: ft.Page, runtime):
        self.page = page
        self.runtime = runtime
        self._course_views = []
        self._urls_from_course_list: List[str] = []

        self._snackbar = ft.SnackBar(content=ft.Text(""), duration=3000)

        self.sidebar = Sidebar(page=page, on_path_changed=self._on_path_changed)
        self.source_selector = SourceSelector(on_source_changed=self._on_source_changed)
        self.pipeline_monitor = PipelineMonitor(
            on_cancel=lambda job: self._job_action('cancel', job),
            on_retry=lambda job: self._job_action('retry', job),
            on_result=lambda job: self._job_action('open_result', job),
            on_copy=lambda job: self._job_action('copy_prompt', job))
        self.log_drawer = LogDrawer(page=page)

        self._build_ui()
        self._load_saved_inputs()
        self._unsubscribe = self.runtime.subscribe(invoke_on_ui(self.page, self._runtime_update))
        for job in self.runtime.jobs():
            self._on_task_updated(job)

    # ── UI 빌드 ───────────────────────────────────────────

    def _build_ui(self):
        header = build_header(
            self.page,
            on_settings_click=lambda e: open_settings_dialog(self.page),
        )

        # ── 메인 콘텐츠 ──────────────────────────────────
        # URL 입력 영역
        self._url_field = ft.TextField(
            label="강의 URL (한 줄에 하나씩)",
            hint_text="https://canvas.ssu.ac.kr/courses/.../modules/items/...",
            multiline=True,
            min_lines=3,
            max_lines=6,
            border_radius=Radius.MD,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            text_size=Typography.BODY,
        )

        # 파일 선택 영역 (파일 소스 선택 시 표시)
        self._picked_files: list[str] = []
        self._file_pick_btn = ft.OutlinedButton(
            content=ft.Text("파일 선택"),
            icon=ft.Icons.UPLOAD_FILE,
            on_click=self._handle_pick_files,
            visible=False,
            style=ft.ButtonStyle(
                color=Colors.PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=Radius.MD),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                text_style=ft.TextStyle(size=Typography.BODY, weight=Typography.SEMI_BOLD),
                side=ft.BorderSide(width=2, color=ft.Colors.with_opacity(0.3, Colors.PRIMARY)),
            ),
        )
        self._file_count_text = ft.Text(
            "", size=Typography.SMALL, color=Colors.TEXT_SECONDARY, visible=False,
        )
        self._file_clear_btn = ft.TextButton(
            content=ft.Text("모두 제거"),
            icon=ft.Icons.DELETE_SWEEP,
            on_click=self._clear_files,
            visible=False,
            style=ft.ButtonStyle(
                color=Colors.ERROR,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                text_style=ft.TextStyle(size=Typography.SMALL),
            ),
        )
        self._file_list = ft.Column(spacing=4, visible=False)
        self._stage_hint_text = ft.Text(
            "", size=Typography.SMALL, color=Colors.PRIMARY, visible=False,
        )

        self._file_input_area = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self._file_pick_btn,
                        self._file_count_text,
                        ft.Container(expand=True),
                        self._file_clear_btn,
                    ],
                    spacing=Spacing.SM,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                self._file_list,
            ],
            spacing=Spacing.SM,
            visible=False,
        )

        # 강의 목록에서 선택 버튼 (LMS 소스 선택 시 표시)
        self._course_list_btn = ft.OutlinedButton(
            content=ft.Text("강의 목록에서 선택"),
            icon=ft.Icons.LIST,
            on_click=self._open_course_list,
            visible=False,
            style=ft.ButtonStyle(
                color=Colors.PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=Radius.MD),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                text_style=ft.TextStyle(size=Typography.BODY, weight=Typography.SEMI_BOLD),
                side=ft.BorderSide(width=2, color=ft.Colors.with_opacity(0.3, Colors.PRIMARY)),
            ),
        )

        # 시작 버튼
        self._start_btn = ft.ElevatedButton(
            content=ft.Text("작업 시작"),
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._handle_start,
            expand=True,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=Colors.PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=Radius.LG),
                padding=ft.padding.symmetric(vertical=14),
                text_style=ft.TextStyle(weight=Typography.SEMI_BOLD, size=14),
                overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            ),
        )
        self._stop_btn = ft.OutlinedButton(
            content=ft.Text("전체 중지"),
            icon=ft.Icons.STOP_CIRCLE,
            on_click=self._handle_queue_stop,
            visible=False,
            style=ft.ButtonStyle(
                color=Colors.ERROR,
                shape=ft.RoundedRectangleBorder(radius=Radius.LG),
                padding=ft.padding.symmetric(vertical=14, horizontal=20),
                text_style=ft.TextStyle(weight=Typography.SEMI_BOLD, size=14),
                side=ft.BorderSide(width=2, color=Colors.ERROR),
            ),
        )

        main_content = ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    ft.Row(
                        controls=[
                            self.sidebar.control,
                            ft.VerticalDivider(width=1, color=Colors.BORDER),
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        # 소스 선택 카드
                                        self.source_selector.control,
                                        # 소스별 입력 영역
                                        self._course_list_btn,
                                        self._url_field,
                                        self._file_input_area,
                                        self._stage_hint_text,
                                        ft.Container(expand=True),
                                        # 액션 바
                                        ft.Row(
                                            controls=[
                                                self._start_btn,
                                                self._stop_btn,
                                            ],
                                            spacing=Spacing.SM,
                                        ),
                                    ],
                                    spacing=Spacing.MD,
                                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                ),
                                expand=True,
                                padding=ft.padding.symmetric(
                                    horizontal=20, vertical=16),
                            ),
                        ],
                        expand=True,
                        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                        spacing=0,
                    ),
                ],
                spacing=0,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            expand=True,
        )

        self.page.add(
            ft.Column(
                controls=[
                    main_content,
                    self.pipeline_monitor.control,
                    self.log_drawer.control,
                ],
                spacing=0,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            )
        )
    # ── 소스 전환 ─────────────────────────────────────────

    def _on_source_changed(self, source: str):
        is_lms = (source == "lms")
        self._course_list_btn.visible = is_lms
        self._url_field.visible = is_lms
        self._file_input_area.visible = not is_lms
        self._update_stage_hint()
        self.log_drawer.append_message(
            "입력 소스: " + ("LMS 강의" if is_lms else "로컬 파일"))
        self.page.update()

    def _on_path_changed(self, path: str):
        self.log_drawer.append_message(f"저장 경로 변경: {path}")

    # ── 파일 선택 ─────────────────────────────────────────

    def _handle_pick_files(self, e=None):
        # FilePicker는 Service로 page.services에 등록 (page당 한 번)
        if not hasattr(self.page, "_fp_files"):
            self.page._fp_files = ft.FilePicker()
            self.page.services.append(self.page._fp_files)
            self.page.update()

        async def _pick():
            # Flet 0.81: pick_files가 결과를 직접 반환 (on_result 콜백 없음)
            files = await self.page._fp_files.pick_files(
                dialog_title="처리할 파일 선택",
                allow_multiple=True,
            )
            if files:
                self._on_files_picked([f.path for f in files])

        self.page.run_task(_pick)

    def _on_files_picked(self, paths: list):
        if not paths:
            return
        existing = set(self._picked_files)
        added = [p for p in paths if p and p not in existing]
        self._picked_files.extend(added)
        self._rebuild_file_list()
        self.page.update()

    def _remove_file(self, path: str):
        if path in self._picked_files:
            self._picked_files.remove(path)
        self._rebuild_file_list()
        self.page.update()

    def _clear_files(self, e=None):
        self._picked_files.clear()
        self._rebuild_file_list()
        self.page.update()

    def _rebuild_file_list(self):
        """선택된 파일 목록 + 파일별 자동 시작 단계 표시"""
        self._file_list.controls.clear()
        for path in self._picked_files:
            stage = self.source_selector.get_stage_label_for_file(path)

            def _make_remove(p=path):
                def _remove(e):
                    self._remove_file(p)
                return _remove

            self._file_list.controls.append(
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.INSERT_DRIVE_FILE, size=14,
                                color=Colors.TEXT_MUTED),
                        ft.Text(
                            Path(path).name, size=Typography.SMALL,
                            color=Colors.TEXT, expand=True, max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS, tooltip=path,
                        ),
                        ft.Container(
                            content=ft.Text(f"{stage}부터", size=Typography.CAPTION,
                                            color=Colors.PRIMARY),
                            bgcolor="#EFF6FF",
                            border_radius=Radius.SM,
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE, icon_size=14,
                            icon_color=Colors.TEXT_MUTED,
                            on_click=_make_remove(), tooltip="제거",
                            style=ft.ButtonStyle(padding=ft.padding.all(2)),
                        ),
                    ],
                    spacing=Spacing.SM,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        has_files = len(self._picked_files) > 0
        self._file_list.visible = has_files
        self._file_count_text.value = f"{len(self._picked_files)}개 선택됨" if has_files else ""
        self._file_count_text.visible = has_files
        self._file_clear_btn.visible = has_files
        self._update_stage_hint()

    def _update_stage_hint(self):
        """파일별 시작 단계 요약 표시"""
        counts: dict[str, int] = {}
        for path in self._picked_files:
            stage = self.source_selector.get_stage_label_for_file(path)
            counts[stage] = counts.get(stage, 0) + 1
        if counts:
            parts = [f"{label} {n}개" for label, n in counts.items()]
            self._stage_hint_text.value = "파일별 자동 단계: " + ", ".join(parts)
            self._stage_hint_text.visible = True
        else:
            self._stage_hint_text.value = ""
            self._stage_hint_text.visible = False

    # ── 강의 목록 ─────────────────────────────────────────

    def _open_course_list(self):
        values = self.sidebar.account.get_values()
        student_id = values.get('student_id', '').strip()
        password = values.get('password', '').strip()

        if not student_id or not password:
            self._show_snackbar("계정 탭에서 학번과 비밀번호를 먼저 입력해주세요.", Colors.WARNING)
            self.sidebar.switch_tab("account")
            return

        course_view = CourseListView(
            self.page,
            username=student_id,
            password=password,
            on_urls_selected=self._on_urls_selected,
        )
        self._course_views.append(course_view)
        course_view.show()

    def _on_urls_selected(self, urls: List[str]):
        existing = set(
            line.strip() for line in (self._url_field.value or "").split('\n')
            if line.strip())
        new_urls = [u for u in urls if u not in existing]
        if new_urls:
            current = (self._url_field.value or "").strip()
            combined = current + '\n' + '\n'.join(new_urls) if current else '\n'.join(new_urls)
            self._url_field.value = combined
        msg = f"강의 목록에서 {len(new_urls)}개 URL이 추가되었습니다."
        if len(urls) - len(new_urls):
            msg += f" (중복 {len(urls) - len(new_urls)}개 제외)"
        self.log_drawer.append_message(msg)
        self.page.update()

    # ── 작업 시작 (큐) ────────────────────────────────────

    def _handle_start(self):
        self.sidebar.clear_errors()

        engine = self.sidebar.ai_settings.get_engine()
        inputs = self.sidebar.get_all_inputs()

        source = self.source_selector.current
        if source is None:
            self._show_snackbar("입력 소스를 선택해주세요.", Colors.WARNING)
            return

        # 입력 수집
        if source == "lms":
            urls = [u.strip() for u in (self._url_field.value or "").split('\n') if u.strip()]
            files = []
            if not urls:
                self._show_snackbar("강의 URL을 입력하거나 목록에서 선택해주세요.", Colors.WARNING)
                return
        else:
            urls = []
            files = self._picked_files
            if not files:
                self._show_snackbar("처리할 파일을 선택해주세요.", Colors.WARNING)
                return

        # 검증 (로컬 파일 소스는 URL/계정/Chrome 검증 불필요)
        is_file = (source != "lms")
        skip_key = engine in ("clipboard", "custom")
        valid, error_message = InputValidator.validate_all_inputs(
            {**inputs, 'urls': '\n'.join(urls)},
            skip_api_key=skip_key,
            skip_urls=is_file,
            require_credentials=not is_file,
            require_chrome=not is_file,
        )
        if not valid:
            self._show_snackbar(error_message, Colors.ERROR)
            return

        self._enqueue(urls, files, inputs)

    def _enqueue(self, urls: List[str], files: List[str], inputs: Dict[str, str]):
        """소스에 따라 큐에 작업 추가"""
        engine = self.sidebar.ai_settings.get_engine()
        model_name = self.sidebar.ai_settings.get_model()
        save_user_inputs({**inputs, 'ai_model': model_name, 'ai_engine': engine})
        set_summary_mode(self.sidebar.get_summary_mode())
        set_subject_category(self.sidebar.get_subject_category())
        set_subject_custom(self.sidebar.get_subject_custom())

        settings = self._build_queue_settings(inputs, engine, model_name)
        files = list(files)
        self._start_btn.disabled = True
        self.page.update()
        async def submit():
            import asyncio
            try:
                job_ids = await asyncio.to_thread(self.runtime.submit, urls, files, settings)
                for job_id in job_ids:
                    self._on_task_updated(self.runtime.service.detail(self.runtime.context, job_id))
                self.log_drawer.append_message(f"작업 추가: URL {len(urls)}개, 파일 {len(files)}개")
                self._url_field.value = ""
                self._picked_files = []
                self._rebuild_file_list()
            except Exception as exc:
                self._show_snackbar(f"작업 추가 실패: {getattr(exc, 'code', type(exc).__name__)}", Colors.ERROR)
            finally:
                self._start_btn.disabled = False
                self.page.update()
        self.page.run_task(submit)

    def _stt_execution_params(self):
        from src.gui.core.file_manager import get_stt_api_key, load_settings
        params = dict(get_stt_params())
        engine = get_stt_engine()
        if engine in ("openai-whisper", "openai-compatible"):
            params["api_key"] = get_stt_api_key(engine)
        if engine == "openai-compatible":
            params["base_url"] = get_stt_api_key("openai-compatible-base-url")
            params["model_name"] = get_stt_api_key("openai-compatible-model")
        if engine == "returnzero":
            saved = load_settings()
            params["client_id"] = saved.get("returnzero_client_id", "")
            params["client_secret"] = saved.get("returnzero_client_secret", "")
        return params

    def _build_queue_settings(self, inputs: Dict, engine: str, model_name: str) -> Dict:
        return {
            'user_inputs': inputs,
            'save_video_dir': ensure_downloads_directory() if self.sidebar.get_save_video() else None,
            'model_name': model_name,
            'engine': engine,
            'base_url': inputs.get('base_url', ''),
            'summary_prompt': get_summary_prompt(),
            'chrome_path': get_chrome_path(),
            'headless': not get_debug_mode(),
            'stt_engine': get_stt_engine(),
            'stt_model': get_stt_model(),
            'stt_params': self._stt_execution_params(),
            'downloads_dir': ensure_downloads_directory(),
        }

    def _on_task_updated(self, task):
        self.pipeline_monitor.update_task(task)
        self._stop_btn.visible = any(job['status'] in ('queued', 'running', 'cancelling')
                                     for job in self.pipeline_monitor._tasks.values())
        self.page.update()

    def _runtime_update(self, job, message):
        if message:
            self.log_drawer.append_message(message)
        if job:
            self._on_task_updated(job)

    def _job_action(self, action, job):
        async def run():
            import asyncio
            try:
                method = getattr(self.runtime, action)
                args = (job['id'], job['current_attempt_id']) if action in ('cancel', 'retry') else (job,)
                await asyncio.to_thread(method, *args)
            except Exception as exc:
                self._show_snackbar(f"작업 처리 실패: {getattr(exc, 'code', type(exc).__name__)}", Colors.ERROR)
        self.page.run_task(run)

    def close(self):
        self._unsubscribe()
        for view in self._course_views:
            view.close()

    def _handle_queue_stop(self):
        def do_stop(e):
            self.runtime.cancel_all()
            confirm_dialog.open = False
            self.page.update()

        def cancel(e):
            confirm_dialog.open = False
            self.page.update()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("확인"),
            content=ft.Text("대기열의 모든 작업을 중지하시겠습니까?"),
            shape=ft.RoundedRectangleBorder(radius=Radius.LG),
            bgcolor=Colors.BG,
            actions=[
                ft.TextButton(content=ft.Text("아니오"), on_click=cancel),
                ft.ElevatedButton(content=ft.Text("예"), on_click=do_stop,
                    style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=Colors.ERROR,
                        shape=ft.RoundedRectangleBorder(radius=Radius.MD))),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(confirm_dialog)

    # ── 유틸리티 ─────────────────────────────────────────

    def _show_snackbar(self, message: str, bgcolor: str = Colors.PRIMARY):
        try:
            self._snackbar.content.value = message
            self._snackbar.bgcolor = bgcolor
            self._snackbar.open = True
            if self._snackbar not in self.page.overlay:
                self.page.overlay.append(self._snackbar)
            self.page.update()
        except Exception:
            pass

    def _load_saved_inputs(self):
        saved = load_user_inputs()
        self.sidebar.load_saved(saved)
        self.page.update()
