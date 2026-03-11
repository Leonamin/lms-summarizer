"""
설정 다이얼로그 (Flet AlertDialog)
"""

import os
import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius, divider
from src.gui.core.file_manager import (
    DEFAULT_PROMPT,
    get_summary_prompt, set_summary_prompt,
    get_chrome_path, set_chrome_path, detect_chrome_paths,
    get_debug_mode, set_debug_mode,
    get_auto_open_folder, set_auto_open_folder,
)


def open_settings_dialog(page: ft.Page):
    """설정 다이얼로그를 열고 닫기까지 관리"""

    prompt_field = ft.TextField(
        value=get_summary_prompt(),
        multiline=True,
        min_lines=3,
        max_lines=6,
        border_radius=Radius.SM,
        border_color=Colors.BORDER,
        focused_border_color=Colors.PRIMARY,
        text_size=Typography.BODY,
        label="요약 프롬프트",
        label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
    )

    chrome_field = ft.TextField(
        value=get_chrome_path(),
        hint_text="Chrome 실행 파일 경로",
        border_radius=Radius.SM,
        border_color=Colors.BORDER,
        focused_border_color=Colors.PRIMARY,
        text_size=Typography.BODY,
        label="Chrome 경로",
        label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
        prefix_icon=ft.Icons.WEB,
    )

    # 자동 감지 경로 버튼들
    detected_paths = detect_chrome_paths()
    detected_controls = []
    if detected_paths:
        detected_controls.append(
            ft.Text("자동 감지된 경로:", size=Typography.SMALL, color=Colors.TEXT_MUTED)
        )
        for p in detected_paths:
            detected_controls.append(
                ft.TextButton(
                    content=ft.Text(p),
                    style=ft.ButtonStyle(
                        color=Colors.PRIMARY,
                        padding=ft.padding.symmetric(horizontal=4, vertical=2),
                        text_style=ft.TextStyle(size=Typography.SMALL),
                    ),
                    on_click=lambda e, path=p: _set_chrome_path(path),
                )
            )

    def _set_chrome_path(path):
        chrome_field.value = path
        chrome_field.update()

    def _reset_prompt(e):
        prompt_field.value = DEFAULT_PROMPT
        prompt_field.update()

    def _close(e):
        dialog.open = False
        page.update()

    debug_switch = ft.Switch(
        value=get_debug_mode(),
        active_color=Colors.PRIMARY,
    )

    auto_open_switch = ft.Switch(
        value=get_auto_open_folder(),
        active_color=Colors.PRIMARY,
    )

    def _save(e):
        prompt = (prompt_field.value or "").strip()
        chrome_path = (chrome_field.value or "").strip()

        set_summary_prompt(prompt if prompt else DEFAULT_PROMPT)
        set_debug_mode(debug_switch.value)
        set_auto_open_folder(auto_open_switch.value)

        if chrome_path:
            if not os.path.exists(chrome_path):
                snackbar = ft.SnackBar(
                    content=ft.Text(f"Chrome 경로가 존재하지 않습니다: {chrome_path}"),
                    bgcolor=Colors.ERROR,
                    open=True,
                )
                page.overlay.append(snackbar)
                page.update()
                return
            set_chrome_path(chrome_path)

        dialog.open = False
        page.update()

    file_picker = ft.FilePicker()

    async def _browse_chrome(e):
        files = await file_picker.pick_files(
            dialog_title="Chrome 실행 파일 선택",
            allowed_extensions=["app", "exe", ""],
        )
        if files:
            _set_chrome_path(files[0].path)

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            controls=[
                ft.Icon(ft.Icons.SETTINGS, size=20, color=Colors.PRIMARY),
                ft.Text("설정", size=Typography.HEADING, weight=Typography.SEMI_BOLD),
            ],
            spacing=Spacing.SM,
        ),
        content=ft.Container(
            width=480,
            content=ft.Column(
                controls=[
                    # 요약 프롬프트 섹션
                    ft.Text(
                        "AI 요약 시 사용되는 프롬프트를 수정할 수 있습니다.",
                        size=Typography.SMALL,
                        color=Colors.TEXT_MUTED,
                    ),
                    prompt_field,
                    ft.TextButton(
                        content=ft.Text("기본값 복원"),
                        icon=ft.Icons.RESTORE,
                        style=ft.ButtonStyle(
                            color=Colors.PRIMARY,
                            text_style=ft.TextStyle(size=Typography.CAPTION),
                        ),
                        on_click=_reset_prompt,
                    ),
                    divider(),
                    # Chrome 경로 섹션
                    ft.Text(
                        "LMS 영상 재생에 사용할 Chrome 경로입니다.",
                        size=Typography.SMALL,
                        color=Colors.TEXT_MUTED,
                    ),
                    ft.Row(
                        controls=[
                            ft.Container(content=chrome_field, expand=True),
                            ft.OutlinedButton(
                                content=ft.Text("찾아보기"),
                                icon=ft.Icons.FOLDER_OPEN,
                                on_click=_browse_chrome,
                                style=ft.ButtonStyle(
                                    color=Colors.PRIMARY,
                                    shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                                ),
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),
                    *detected_controls,
                    divider(),
                    # 디버그 모드 섹션
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("디버그 모드", size=Typography.BODY, weight=Typography.SEMI_BOLD),
                                    ft.Text(
                                        "브라우저 창을 표시하여 동작을 확인합니다.",
                                        size=Typography.SMALL,
                                        color=Colors.TEXT_MUTED,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            debug_switch,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    divider(),
                    # 완료 후 폴더 자동 열기 섹션
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("완료 후 폴더 자동 열기", size=Typography.BODY, weight=Typography.SEMI_BOLD),
                                    ft.Text(
                                        "작업 완료 시 결과 폴더를 자동으로 엽니다.",
                                        size=Typography.SMALL,
                                        color=Colors.TEXT_MUTED,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            auto_open_switch,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=Spacing.MD,
                tight=True,
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        ),
        actions=[
            ft.TextButton(content=ft.Text("취소"), on_click=_close),
            ft.ElevatedButton(
                content=ft.Text("저장"),
                icon=ft.Icons.SAVE,
                on_click=_save,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=Colors.PRIMARY,
                    shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                ),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.show_dialog(dialog)
