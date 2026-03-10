"""
메인 뷰 (Flet)
"""

import subprocess
import sys
from typing import Dict, List

import flet as ft

from src.gui.theme import (
    Colors, Typography, Spacing, Radius,
    card_container, section_title, caption_text,
    primary_button, outline_button, danger_button,
    CARD_SHADOW,
)
from src.gui.config.constants import APP_TITLE, APP_VERSION, Messages
from src.gui.config.settings import INPUT_FIELD_CONFIGS
from src.gui.core.validators import InputValidator
from src.gui.core.module_loader import check_required_modules
from src.gui.core.file_manager import (
    ensure_downloads_directory, set_downloads_directory,
    save_user_inputs, load_user_inputs,
)
from src.gui.components.input_field import InputField
from src.gui.components.log_area import LogArea
from src.gui.components.model_selector import ModelSelector
from src.gui.views.progress_view import ProgressModal
from src.gui.views.settings_view import open_settings_dialog
from src.gui.views.course_list_view import CourseListView
from src.gui.workers.processing_worker import ProcessingWorker


class MainView:
    """메인 뷰 클래스"""

    def __init__(self, page: ft.Page, modules: Dict, module_errors: List[str]):
        self.page = page
        self.modules = modules
        self.module_errors = module_errors

        self.input_fields: Dict[str, InputField] = {}
        self.log_area = LogArea()
        self.model_selector = ModelSelector()
        self.worker: ProcessingWorker = None
        self.modal: ProgressModal = None

        # 상태
        self._is_processing = False

        # 스레드 안전한 SnackBar (미리 생성하여 재사용)
        self._snackbar = ft.SnackBar(content=ft.Text(""), duration=3000)
        page.overlay.append(self._snackbar)

        # 컨트롤 생성
        self._save_video_checkbox = ft.Checkbox(
            label="처리 완료 후 원본 동영상 보관 (미선택 시 자동 삭제)",
            value=False,
            active_color=Colors.PRIMARY,
        )

        self._start_btn = ft.ElevatedButton(
            content=ft.Text("요약 시작"),
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._handle_start,
            expand=True,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=Colors.PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                padding=ft.padding.symmetric(vertical=14),
                text_style=ft.TextStyle(weight=Typography.SEMI_BOLD, size=14),
                overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            ),
        )

        self._clear_btn = ft.OutlinedButton(
            content=ft.Text("초기화"),
            icon=ft.Icons.DELETE_OUTLINE,
            on_click=self._handle_clear,
            style=ft.ButtonStyle(
                color=Colors.ERROR,
                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                padding=ft.padding.symmetric(vertical=14, horizontal=16),
                text_style=ft.TextStyle(weight=Typography.SEMI_BOLD, size=13),
                side=ft.BorderSide(width=1, color=Colors.ERROR),
            ),
        )

        self._path_text = ft.Text(
            ensure_downloads_directory(),
            size=Typography.CAPTION,
            color=Colors.TEXT_SECONDARY,
            expand=True,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        self._folder_picker = ft.FilePicker()

        # 입력 필드 생성
        for name, config in INPUT_FIELD_CONFIGS.items():
            self.input_fields[name] = InputField(config)

        # UI 빌드
        self._build_ui()
        self._load_saved_inputs()
        self._check_module_status()

    def _build_ui(self):
        """전체 UI 레이아웃 구성"""
        self.page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        self._build_header(),
                        self._build_path_section(),
                        self._build_form_card(),
                        self.log_area.control,
                        self._build_action_bar(),
                    ],
                    spacing=Spacing.SM,
                    expand=True,
                ),
                padding=ft.padding.symmetric(horizontal=20, vertical=16),
                expand=True,
            )
        )

    def _build_header(self) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.SCHOOL, size=22, color=Colors.PRIMARY),
                            ft.Text(
                                APP_TITLE,
                                size=Typography.TITLE,
                                weight=Typography.BOLD,
                                color=Colors.TEXT,
                                expand=True,
                            ),
                            ft.Text(
                                APP_VERSION,
                                size=Typography.SMALL,
                                color=Colors.TEXT_MUTED,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.SETTINGS,
                                icon_color=Colors.TEXT_SECONDARY,
                                icon_size=20,
                                tooltip="설정",
                                on_click=lambda e: open_settings_dialog(self.page),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Text(
                        "숭실대학교 LMS 강의 동영상을 다운로드하고 AI로 요약합니다.",
                        size=Typography.CAPTION,
                        color=Colors.TEXT_MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _build_path_section(self) -> ft.Container:
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.FOLDER, size=16, color=Colors.TEXT_MUTED),
                    ft.Text("저장 경로:", size=Typography.CAPTION, weight=Typography.SEMI_BOLD, color=Colors.TEXT_SECONDARY),
                    ft.Container(
                        content=self._path_text,
                        bgcolor=Colors.CARD,
                        border_radius=Radius.SM,
                        border=ft.border.all(1, Colors.BORDER),
                        padding=ft.padding.symmetric(horizontal=10, vertical=6),
                        expand=True,
                    ),
                    ft.OutlinedButton(
                        content=ft.Text("열기"),
                        icon=ft.Icons.FOLDER_OPEN,
                        on_click=self._open_in_finder,
                        style=ft.ButtonStyle(
                            color=Colors.PRIMARY,
                            shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                            padding=ft.padding.symmetric(horizontal=12, vertical=8),
                            text_style=ft.TextStyle(size=Typography.CAPTION),
                        ),
                    ),
                    ft.OutlinedButton(
                        content=ft.Text("변경"),
                        on_click=self._change_path,
                        style=ft.ButtonStyle(
                            color=Colors.PRIMARY,
                            shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                            padding=ft.padding.symmetric(horizontal=12, vertical=8),
                            text_style=ft.TextStyle(size=Typography.CAPTION),
                        ),
                    ),
                ],
                spacing=Spacing.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=4),
        )

    def _build_form_card(self) -> ft.Container:
        """입력 폼 카드"""
        form_controls = [ft.Container(height=2)]

        for name, config in INPUT_FIELD_CONFIGS.items():
            field = self.input_fields[name]

            if name == 'urls':
                # URL 필드: 라벨 옆에 "강의 목록에서 선택" 버튼
                form_controls.append(
                    ft.Row(
                        controls=[
                            ft.Container(expand=True),
                            ft.OutlinedButton(
                                content=ft.Text("강의 목록에서 선택"),
                                icon=ft.Icons.MENU_BOOK,
                                on_click=self._open_course_list,
                                style=ft.ButtonStyle(
                                    color=Colors.PRIMARY,
                                    shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                    text_style=ft.TextStyle(size=Typography.CAPTION),
                                ),
                            ),
                        ],
                    )
                )

            form_controls.append(field.container)

            # API 키 다음에 모델 선택기
            if name == 'api_key':
                form_controls.append(self.model_selector.control)

        return card_container(
            content=ft.Column(
                controls=form_controls,
                spacing=Spacing.SM,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
        )

    def _build_action_bar(self) -> ft.Container:
        """하단 고정 액션 바 (체크박스 + 버튼)"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    self._save_video_checkbox,
                    ft.Row(
                        controls=[self._start_btn, self._clear_btn],
                        spacing=Spacing.SM,
                    ),
                ],
                spacing=Spacing.XS,
            ),
            padding=ft.padding.only(top=4),
        )

    # ── 이벤트 핸들러 ──────────────────────────────────────

    def _open_in_finder(self, e=None):
        path = ensure_downloads_directory()
        if sys.platform == 'darwin':
            subprocess.Popen(['open', path])
        elif sys.platform == 'win32':
            subprocess.Popen(['explorer', path])
        else:
            subprocess.Popen(['xdg-open', path])

    def _change_path(self, e=None):
        path = self._folder_picker.get_directory_path(
            dialog_title="저장 경로 선택",
            initial_directory=ensure_downloads_directory(),
        )
        if path:
            try:
                set_downloads_directory(path)
                self._path_text.value = path
                self.log_area.append_message(f"저장 경로 변경: {path}")
                self.page.update()
            except Exception as ex:
                self._show_snackbar(f"경로 변경 오류: {str(ex)}", Colors.ERROR)

    def _open_course_list(self, e=None):
        student_id = self.input_fields['student_id'].get_value().strip()
        password = self.input_fields['password'].get_value().strip()

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
        current = self.input_fields['urls'].get_value().strip()
        existing = set(line.strip() for line in current.split('\n') if line.strip()) if current else set()

        new_urls = [u for u in urls if u not in existing]
        skipped = len(urls) - len(new_urls)

        if new_urls:
            if current:
                combined = current + '\n' + '\n'.join(new_urls)
            else:
                combined = '\n'.join(new_urls)
            self.input_fields['urls'].set_value(combined)
            self.input_fields['urls'].control.update()

        msg = f"강의 목록에서 {len(new_urls)}개 URL이 추가되었습니다."
        if skipped:
            msg += f" (중복 {skipped}개 제외)"
        self.log_area.append_message(msg)
        self.page.update()

    def _handle_start(self, e=None):
        if self._is_processing:
            self._handle_stop()
            return

        inputs = {name: field.get_value() for name, field in self.input_fields.items()}
        valid, error_message = InputValidator.validate_all_inputs(inputs)
        if not valid:
            self._show_snackbar(error_message, Colors.ERROR)
            return

        all_loaded, missing = check_required_modules(self.modules)
        if not all_loaded:
            self._show_snackbar(f"{Messages.MODULE_LOAD_ERROR}: {', '.join(missing)}", Colors.ERROR)
            return

        self._start_processing(inputs)

    def _start_processing(self, inputs: Dict[str, str]):
        model_name = self.model_selector.get_model()
        save_user_inputs({**inputs, 'ai_model': model_name})

        self._is_processing = True
        self._start_btn.text = "중지"
        self._start_btn.icon = ft.Icons.STOP
        self._start_btn.style = ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=Colors.ERROR,
            shape=ft.RoundedRectangleBorder(radius=Radius.SM),
            padding=ft.padding.symmetric(vertical=14),
            text_style=ft.TextStyle(weight=Typography.SEMI_BOLD, size=14),
        )
        self._clear_btn.disabled = True
        self._set_fields_enabled(False)
        self.log_area.clear()

        save_video_dir = ensure_downloads_directory() if self._save_video_checkbox.value else None

        # 프로그레스 모달 생성
        self.modal = ProgressModal(self.page, on_stop=self._on_modal_stop)

        def on_log(msg):
            self.log_area.append_message(msg)
            if self.modal:
                self.modal.append_log(msg)
            try:
                self.page.update()
            except Exception:
                pass

        def on_finished(success, message):
            try:
                self._is_processing = False
                self._start_btn.text = "요약 시작"
                self._start_btn.icon = ft.Icons.PLAY_ARROW
                self._start_btn.style = ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=Colors.PRIMARY,
                    shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                    padding=ft.padding.symmetric(vertical=14),
                    text_style=ft.TextStyle(weight=Typography.SEMI_BOLD, size=14),
                    overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                )
                self._clear_btn.disabled = False
                self._set_fields_enabled(True)

                if self.modal:
                    if success:
                        self.modal.mark_complete()
                    else:
                        self.modal.mark_cancelled()

                if success:
                    self._show_snackbar("작업이 완료되었습니다!", Colors.SUCCESS)
                elif "취소" not in message:
                    self._show_snackbar(f"오류: {message}", Colors.ERROR)
                else:
                    # 취소 시에도 UI 갱신
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
            on_log=on_log,
            on_finished=on_finished,
            on_step_changed=on_step,
            on_progress=on_progress,
        )

        self.modal.show()
        self.page.update()
        self.worker.start()

    def _handle_stop(self):
        def do_stop(e):
            if self.worker:
                self.worker.request_cancel()
                self.log_area.append_message("⚠️ 작업 중지를 요청했습니다...")
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
        self.page.open(confirm_dialog)

    def _on_modal_stop(self):
        if self.worker:
            self.worker.request_cancel()
            self.log_area.append_message("⚠️ 작업 중지를 요청했습니다...")

    def _handle_clear(self, e=None):
        def do_clear(e):
            for field in self.input_fields.values():
                field.clear()
            self.log_area.clear()
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
        self.page.open(confirm_dialog)

    # ── 유틸리티 ─────────────────────────────────────────────

    def _show_snackbar(self, message: str, bgcolor: str = Colors.PRIMARY):
        """스레드 안전한 SnackBar 표시 (미리 생성된 컨트롤 재사용)"""
        try:
            self._snackbar.content.value = message
            self._snackbar.bgcolor = bgcolor
            self._snackbar.open = True
            self.page.update()
        except Exception:
            pass

    def _set_fields_enabled(self, enabled: bool):
        for field in self.input_fields.values():
            field.set_enabled(enabled)
        self.model_selector.set_enabled(enabled)

    def _check_module_status(self):
        if self.module_errors:
            self.log_area.append_message("⚠️ 일부 모듈 로드 실패:")
            for error in self.module_errors:
                self.log_area.append_message(f"   - {error}")
            self.log_area.append_message(Messages.INSTALL_REQUIREMENTS)
            self.page.update()

    def _load_saved_inputs(self):
        saved = load_user_inputs()
        for field_name, value in saved.items():
            if field_name in self.input_fields and value:
                self.input_fields[field_name].set_value(value)
        if 'ai_model' in saved:
            self.model_selector.set_model(saved['ai_model'])
        self.page.update()
