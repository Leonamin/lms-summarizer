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
from src.gui.core.module_loader import check_required_modules
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
from src.gui.workers.queue_manager import QueueManager
from src.pipeline_stage import PipelineStage


class MainView:
    """메인 뷰 — 큐 중심 재구성"""

    def __init__(self, page: ft.Page, modules: Dict, module_errors: List[str]):
        self.page = page
        self.modules = modules
        self.module_errors = module_errors
        self.queue_manager: QueueManager = None
        self._urls_from_course_list: List[str] = []

        self._snackbar = ft.SnackBar(content=ft.Text(""), duration=3000)

        self.sidebar = Sidebar(page=page, on_path_changed=self._on_path_changed)
        self.source_selector = SourceSelector(on_source_changed=self._on_source_changed)
        self.pipeline_monitor = PipelineMonitor()
        self.log_drawer = LogDrawer(page=page)

        self._build_ui()
        self._load_saved_inputs()
        self._check_module_status()

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
        self._file_list_text = ft.Text(
            "", size=Typography.SMALL, color=Colors.TEXT_SECONDARY, visible=False,
        )
        self._stage_hint_text = ft.Text(
            "", size=Typography.SMALL, color=Colors.PRIMARY, visible=False,
        )

        self._file_input_area = ft.Column(
            controls=[
                self._file_pick_btn,
                self._file_list_text,
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
        self._stage_hint_text.visible = False
        self.page.update()

    def _on_path_changed(self, path: str):
        self.log_drawer.append_message(f"저장 경로 변경: {path}")

    # ── 파일 선택 ─────────────────────────────────────────

    def _handle_pick_files(self, e=None):
        def result_handler(files: list[ft.FilePickerResultFile]):
            if not files:
                return
            self._picked_files = [f.path for f in files if f.path]
            names = [Path(p).name for p in self._picked_files]
            self._file_list_text.value = f"{len(names)}개 파일: " + ", ".join(names[:5]) + ("..." if len(names) > 5 else "")
            self._file_list_text.visible = True
            hint = self.source_selector.get_stage_hint(self._picked_files)
            self._stage_hint_text.value = hint
            self._stage_hint_text.visible = bool(hint)
            self.page.update()

        picker = ft.FilePicker(on_result=result_handler)
        self.page.overlay.append(picker)
        self.page.update()
        picker.pick_files(allow_multiple=True)

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

        # 검증
        skip_key = engine in ("clipboard", "custom")
        valid, error_message = InputValidator.validate_all_inputs(
            {**inputs, 'urls': '\n'.join(urls)}, skip_api_key=skip_key,
        )
        if not valid:
            self._show_snackbar(error_message, Colors.ERROR)
            return

        all_loaded, missing = check_required_modules(self.modules)
        if not all_loaded:
            self._show_snackbar(f"{Messages.MODULE_LOAD_ERROR}: {', '.join(missing)}", Colors.ERROR)
            return

        self._enqueue(urls, files, inputs)

    def _enqueue(self, urls: List[str], files: List[str], inputs: Dict[str, str]):
        """소스에 따라 큐에 작업 추가"""
        engine = self.sidebar.ai_settings.get_engine()
        model_name = self.sidebar.ai_settings.get_model()
        start_stage = self.source_selector.get_start_stage(files)
        save_user_inputs({**inputs, 'ai_model': model_name, 'ai_engine': engine})
        set_summary_mode(self.sidebar.get_summary_mode())
        set_subject_category(self.sidebar.get_subject_category())
        set_subject_custom(self.sidebar.get_subject_custom())

        if self.queue_manager is None:
            self.queue_manager = QueueManager(
                self.modules,
                on_log=invoke_on_ui(self.page, lambda m: self.log_drawer.append_message(m)),
                on_task_updated=invoke_on_ui(self.page, self._on_task_updated),
                on_idle_changed=invoke_on_ui(self.page, self._on_queue_idle),
            )

        settings = self._build_queue_settings(inputs, engine, model_name)
        self.log_drawer.append_message(
            f"작업 추가: URL {len(urls)}개, 파일 {len(files)}개 (시작 단계: {start_stage.value}단계)")

        if urls:
            tasks = self.queue_manager.submit(urls, settings)
            for task in tasks:
                self.pipeline_monitor.update_task(task)
            # 제출된 URL 입력란 비움
            self._url_field.value = ""

        if files:
            self._enqueue_files(files, settings, start_stage)

        self._stop_btn.visible = True
        self.page.update()

    def _enqueue_files(self, files: List[str], settings: Dict, start_stage: PipelineStage):
        """파일 소스 처리 — 시작 단계에 따라 처리 큐에 직접 투입"""
        stage_name = {
            PipelineStage.CONVERT_AUDIO: "변환",
            PipelineStage.STT: "STT",
            PipelineStage.SUMMARIZE: "요약",
        }.get(start_stage, "변환")

        tasks = self.queue_manager.submit_files(files, settings, stage_name)
        for task in tasks:
            self.pipeline_monitor.update_task(task)
        # 선택 파일 초기화
        self._picked_files = []
        self._file_list_text.value = ""
        self._file_list_text.visible = False

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
            'stt_params': get_stt_params(),
        }

    def _on_task_updated(self, task):
        self.pipeline_monitor.update_task(task)
        self.page.update()

    def _on_queue_idle(self, running: bool):
        self._stop_btn.visible = bool(self.queue_manager and self.queue_manager.is_running())
        if not running:
            self._show_snackbar("모든 작업이 완료되었습니다.", Colors.PRIMARY)
        self.page.update()

    def _handle_queue_stop(self):
        def do_stop(e):
            if self.queue_manager:
                self.queue_manager.request_stop()
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

    def _check_module_status(self):
        if self.module_errors:
            self.log_drawer.append_message("일부 모듈 로드 실패:")
            for error in self.module_errors:
                self.log_drawer.append_message(f"   - {error}")
            self.log_drawer.append_message(Messages.INSTALL_REQUIREMENTS)
            self.page.update()

    def _load_saved_inputs(self):
        saved = load_user_inputs()
        self.sidebar.load_saved(saved)
        self.page.update()
