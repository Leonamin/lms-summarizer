"""
설정 다이얼로그 (Flet AlertDialog)
- 요약 프롬프트, Chrome 경로 (기본)
- 고급 설정 접힘/펼침: STT 엔진, 디버그 모드, 폴더 자동 열기
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
    get_stt_engine, set_stt_engine,
    get_stt_api_key, set_stt_api_key,
)


# STT 엔진 옵션
_STT_OPTIONS = [
    ("whisper-cpp", "whisper-cpp (로컬, 무료)"),
    ("returnzero", "ReturnZero API (유료, 높은 정확도)"),
]


def open_settings_dialog(page: ft.Page):
    """설정 다이얼로그를 열고 닫기까지 관리"""

    # ── 요약 프롬프트 ────────────────────────────────────
    prompt_field = ft.TextField(
        value=get_summary_prompt(),
        multiline=True,
        min_lines=3,
        max_lines=6,
        border_radius=Radius.MD,
        border_color=Colors.BORDER,
        focused_border_color=Colors.PRIMARY,
        text_size=Typography.BODY,
        label="요약 프롬프트",
        label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
    )

    def _reset_prompt(e):
        prompt_field.value = DEFAULT_PROMPT
        prompt_field.update()

    # ── Chrome 경로 ──────────────────────────────────────
    chrome_field = ft.TextField(
        value=get_chrome_path(),
        hint_text="Chrome 실행 파일 경로",
        border_radius=Radius.MD,
        border_color=Colors.BORDER,
        focused_border_color=Colors.PRIMARY,
        text_size=Typography.BODY,
        label="Chrome 경로",
        label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
        prefix_icon=ft.Icons.WEB,
    )

    detected_paths = detect_chrome_paths()
    detected_controls = []
    if detected_paths:
        for p in detected_paths:
            detected_controls.append(
                ft.TextButton(
                    content=ft.Text(f"자동 감지된 경로 사용: {p}", size=Typography.SMALL),
                    style=ft.ButtonStyle(
                        color=Colors.PRIMARY,
                        padding=ft.padding.symmetric(horizontal=4, vertical=2),
                    ),
                    on_click=lambda e, path=p: _set_chrome_path(path),
                )
            )
    else:
        detected_controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=16, color="#B45309"),
                                ft.Text(
                                    "Chrome이 감지되지 않았습니다.",
                                    size=Typography.BODY,
                                    weight=Typography.SEMI_BOLD,
                                    color="#B45309",
                                ),
                            ],
                            spacing=Spacing.XS,
                        ),
                        ft.Text(
                            "LMS 영상 재생을 위해 Google Chrome이 필요합니다.\n"
                            "아래 버튼으로 Chrome을 다운로드하거나, 이미 설치된 경우 '찾아보기'로 직접 경로를 지정하세요.",
                            size=Typography.SMALL,
                            color="#92400E",
                        ),
                        ft.TextButton(
                            content=ft.Text("Chrome 다운로드 페이지 열기", size=Typography.SMALL),
                            icon=ft.Icons.OPEN_IN_NEW,
                            style=ft.ButtonStyle(
                                color=Colors.PRIMARY,
                                padding=ft.padding.symmetric(horizontal=4, vertical=2),
                            ),
                            url="https://www.google.com/chrome/",
                        ),
                    ],
                    spacing=4,
                ),
                bgcolor="#FFFBEB",
                border=ft.border.all(1, "#FDE68A"),
                border_radius=Radius.MD,
                padding=ft.padding.all(Spacing.SM),
            )
        )

    def _set_chrome_path(path):
        chrome_field.value = path
        chrome_field.update()

    file_picker = ft.FilePicker()

    async def _browse_chrome(e):
        files = await file_picker.pick_files(
            dialog_title="Chrome 실행 파일 선택",
            allowed_extensions=["app", "exe", ""],
        )
        if files:
            _set_chrome_path(files[0].path)

    # ── 고급 설정: STT 엔진 ──────────────────────────────
    current_stt = get_stt_engine()

    stt_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(key=k, text=t) for k, t in _STT_OPTIONS],
        value=current_stt,
        label="STT 엔진",
        leading_icon=ft.Icons.MIC,
        border_radius=Radius.MD,
        border_color=Colors.BORDER,
        focused_border_color=Colors.PRIMARY,
        text_size=Typography.BODY,
        label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
        on_select=lambda e: _on_stt_changed(),
        dense=True,
    )

    stt_api_key_field = ft.TextField(
        value=get_stt_api_key(),
        hint_text="client_id:client_secret",
        border_radius=Radius.MD,
        border_color=Colors.BORDER,
        focused_border_color=Colors.PRIMARY,
        text_size=Typography.BODY,
        label="ReturnZero API 키",
        label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
        prefix_icon=ft.Icons.KEY,
        visible=(current_stt == "returnzero"),
    )

    stt_description = ft.Text(
        _get_stt_description(current_stt),
        size=Typography.SMALL,
        color=Colors.TEXT_MUTED,
    )

    def _on_stt_changed():
        engine = stt_dropdown.value or "whisper-cpp"
        stt_api_key_field.visible = (engine == "returnzero")
        stt_description.value = _get_stt_description(engine)
        if stt_api_key_field.page:
            stt_api_key_field.update()
        if stt_description.page:
            stt_description.update()

    # ── 고급 설정: 토글 스위치들 ─────────────────────────
    debug_switch = ft.Switch(
        value=get_debug_mode(),
        active_color=Colors.PRIMARY,
    )

    auto_open_switch = ft.Switch(
        value=get_auto_open_folder(),
        active_color=Colors.PRIMARY,
    )

    # ── 고급 설정 접힘/펼침 ──────────────────────────────
    advanced_expanded = False

    advanced_content = ft.Column(
        controls=[
            # STT 엔진
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.MIC, size=16, color=Colors.TEXT_SECONDARY),
                    ft.Text("STT 엔진", size=Typography.BODY, weight=Typography.SEMI_BOLD, color=Colors.TEXT),
                ],
                spacing=Spacing.XS,
            ),
            stt_dropdown,
            stt_api_key_field,
            stt_description,
            divider(),
            # 디버그 모드
            ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.BUG_REPORT, size=16, color=Colors.TEXT_SECONDARY),
                                    ft.Text("디버그 모드", size=Typography.BODY, weight=Typography.SEMI_BOLD, color=Colors.TEXT),
                                ],
                                spacing=Spacing.XS,
                            ),
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
            # 완료 후 폴더 자동 열기
            ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.FOLDER_OPEN, size=16, color=Colors.TEXT_SECONDARY),
                                    ft.Text("완료 후 폴더 자동 열기", size=Typography.BODY, weight=Typography.SEMI_BOLD, color=Colors.TEXT),
                                ],
                                spacing=Spacing.XS,
                            ),
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
        visible=False,
    )

    advanced_chevron = ft.Icon(ft.Icons.EXPAND_MORE, size=18, color=Colors.TEXT_SECONDARY)

    def _toggle_advanced(e):
        nonlocal advanced_expanded
        advanced_expanded = not advanced_expanded
        advanced_content.visible = advanced_expanded
        advanced_chevron.icon = ft.Icons.EXPAND_LESS if advanced_expanded else ft.Icons.EXPAND_MORE
        page.update()

    advanced_header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.TUNE, size=18, color=Colors.TEXT_SECONDARY),
                ft.Text(
                    "고급 설정",
                    size=Typography.BODY,
                    weight=Typography.SEMI_BOLD,
                    color=Colors.TEXT_SECONDARY,
                    expand=True,
                ),
                advanced_chevron,
            ],
            spacing=Spacing.SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        on_click=_toggle_advanced,
        border_radius=Radius.MD,
        border=ft.border.all(1, Colors.BORDER),
        padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=Spacing.SM),
        ink=True,
    )

    # ── 저장/닫기 ────────────────────────────────────────
    def _close(e):
        dialog.open = False
        page.update()

    def _save(e):
        prompt = (prompt_field.value or "").strip()
        chrome_path = (chrome_field.value or "").strip()

        set_summary_prompt(prompt if prompt else DEFAULT_PROMPT)
        set_debug_mode(debug_switch.value)
        set_auto_open_folder(auto_open_switch.value)

        # STT 엔진 저장
        stt_engine = stt_dropdown.value or "whisper-cpp"
        set_stt_engine(stt_engine)
        if stt_engine == "returnzero":
            set_stt_api_key((stt_api_key_field.value or "").strip())

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

    # ── 다이얼로그 조립 ──────────────────────────────────
    dialog = ft.AlertDialog(
        modal=True,
        shape=ft.RoundedRectangleBorder(radius=Radius.LG),
        bgcolor=Colors.BG,
        title=ft.Row(
            controls=[
                ft.Icon(ft.Icons.SETTINGS, size=20, color=Colors.PRIMARY),
                ft.Text("설정", size=Typography.HEADING, weight=Typography.SEMI_BOLD, expand=True),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=18,
                    icon_color=Colors.TEXT_MUTED,
                    on_click=_close,
                    tooltip="닫기",
                ),
            ],
            spacing=Spacing.SM,
        ),
        content=ft.Container(
            width=500,
            content=ft.Column(
                controls=[
                    # 요약 프롬프트 섹션
                    ft.Text(
                        "요약 프롬프트",
                        size=Typography.BODY,
                        weight=Typography.SEMI_BOLD,
                        color=Colors.TEXT,
                    ),
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
                            color=Colors.ACCENT,
                            text_style=ft.TextStyle(size=Typography.CAPTION),
                        ),
                        on_click=_reset_prompt,
                    ),
                    divider(),
                    # Chrome 경로 섹션
                    ft.Text(
                        "Chrome 경로",
                        size=Typography.BODY,
                        weight=Typography.SEMI_BOLD,
                        color=Colors.TEXT,
                    ),
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
                                    shape=ft.RoundedRectangleBorder(radius=Radius.MD),
                                ),
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),
                    *detected_controls,
                    divider(),
                    # 고급 설정 (접힘/펼침)
                    advanced_header,
                    advanced_content,
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
                    shape=ft.RoundedRectangleBorder(radius=Radius.LG),
                ),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.show_dialog(dialog)


def _get_stt_description(engine: str) -> str:
    """STT 엔진별 설명 텍스트"""
    if engine == "returnzero":
        return "ReturnZero는 클라우드 API로 높은 정확도를 제공하지만 유료입니다. ffmpeg 설치가 필요합니다."
    return "whisper-cpp는 로컬에서 실행되며 인터넷 없이 무료로 동작합니다."
