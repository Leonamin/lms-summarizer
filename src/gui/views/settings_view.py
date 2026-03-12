"""
설정 다이얼로그 (Flet AlertDialog)
- 요약 프롬프트 모드/분야 설정 + 프리뷰, Chrome 경로 (기본)
- 고급 설정 접힘/펼침: STT 엔진, 디버그 모드, 폴더 자동 열기
"""

import os
import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius, divider
from src.gui.core.file_manager import (
    get_summary_mode, set_summary_mode,
    get_subject_category, set_subject_category,
    get_subject_custom, set_subject_custom,
    get_chrome_path, set_chrome_path, detect_chrome_paths,
    get_debug_mode, set_debug_mode,
    get_auto_open_folder, set_auto_open_folder,
    get_stt_engine, set_stt_engine,
    get_stt_api_key, set_stt_api_key,
    get_stt_model, set_stt_model,
    get_stt_params, set_stt_params,
)
from src.summarize_pipeline.prompts import (
    SummaryMode, SUMMARY_MODE_LABELS, SUBJECT_CATEGORIES,
    build_prompt,
)


# STT 엔진 옵션
_STT_OPTIONS = [
    ("whisper-cpp", "whisper-cpp (로컬, 무료)"),
    ("returnzero", "ReturnZero API (유료, 높은 정확도)"),
]

# whisper-cpp 모델 옵션 (크기 오름차순)
_STT_MODELS = [
    ("tiny",           "Tiny (39M) — 가장 빠름"),
    ("base",           "Base (74M) — 기본"),
    ("small",          "Small (244M)"),
    ("medium",         "Medium (769M)"),
    ("large-v3-turbo", "Large-v3-turbo (809M) ⭐ 추천"),
    ("large-v3",       "Large-v3 (1.5GB) — 최고 품질"),
]


def open_settings_dialog(page: ft.Page):
    """설정 다이얼로그를 열고 닫기까지 관리"""

    # ── 요약 프롬프트 모드/분야 설정 ──────────────────────
    mode_dropdown = ft.Dropdown(
        options=[
            ft.dropdown.Option(key=k, text=v)
            for k, v in SUMMARY_MODE_LABELS.items()
        ],
        value=get_summary_mode(),
        label="요약 모드",
        border_radius=Radius.MD,
        border_color=Colors.BORDER,
        focused_border_color=Colors.PRIMARY,
        text_size=Typography.BODY,
        label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
        dense=True,
        on_select=lambda e: _update_preview(),
    )

    subject_dropdown = ft.Dropdown(
        options=[
            ft.dropdown.Option(key=k, text=k)
            for k in SUBJECT_CATEGORIES.keys()
        ],
        value=get_subject_category(),
        label="강의 분야",
        border_radius=Radius.MD,
        border_color=Colors.BORDER,
        focused_border_color=Colors.PRIMARY,
        text_size=Typography.BODY,
        label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
        dense=True,
        on_select=lambda e: _update_preview(),
    )

    subject_custom_field = ft.TextField(
        value=get_subject_custom(),
        hint_text="과목명 직접 입력 (선택사항, 드롭다운보다 우선)",
        border_radius=Radius.MD,
        border_color=Colors.BORDER,
        focused_border_color=Colors.PRIMARY,
        text_size=Typography.BODY,
        label="직접 입력",
        label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
        dense=True,
        on_change=lambda e: _update_preview(),
    )

    # 프롬프트 프리뷰 (읽기 전용)
    prompt_preview = ft.TextField(
        value=build_prompt(
            mode=get_summary_mode(),
            subject_category=get_subject_category(),
            subject_custom=get_subject_custom(),
        ),
        multiline=True,
        min_lines=3,
        max_lines=6,
        border_radius=Radius.MD,
        border_color=Colors.BORDER,
        text_size=Typography.SMALL,
        label="생성된 프롬프트 (미리보기)",
        label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
        read_only=True,
    )

    def _update_preview():
        mode = mode_dropdown.value or SummaryMode.NORMAL
        category = subject_dropdown.value or "자동 감지"
        custom = (subject_custom_field.value or "").strip()
        prompt_preview.value = build_prompt(
            mode=mode,
            subject_category=category,
            subject_custom=custom,
        )
        if prompt_preview.page:
            prompt_preview.update()

    def _reset_prompt(e):
        mode_dropdown.value = SummaryMode.NORMAL
        subject_dropdown.value = "자동 감지"
        subject_custom_field.value = ""
        _update_preview()
        if mode_dropdown.page:
            mode_dropdown.update()
            subject_dropdown.update()
            subject_custom_field.update()

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

    # FilePicker는 page당 한 번만 overlay에 등록해야 함
    # 재호출 시 기존 인스턴스를 재사용
    if not hasattr(page, "_fp_chrome"):
        page._fp_chrome = ft.FilePicker()
        page.services.append(page._fp_chrome)
        page.update()
    file_picker = page._fp_chrome

    async def _browse_chrome(e):
        files = await file_picker.pick_files(
            dialog_title="Chrome 실행 파일 선택",
            allowed_extensions=["app", "exe", ""],
        )
        if files:
            _set_chrome_path(files[0].path)

    # ── 고급 설정: STT 엔진 ──────────────────────────────
    import threading as _threading
    from src.audio_pipeline.model_manager import (
        MODEL_REGISTRY, MODE_ORDER, is_available, download_model, DownloadCancelled,
    )

    current_stt = get_stt_engine()
    current_stt_model = get_stt_model()
    current_params = get_stt_params()

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

    # ── 모드 버튼 (3개) ─────────────────────────────────
    _selected_mode = [current_stt_model if current_stt_model in MODE_ORDER else "base"]
    _download_cancel: list = [None]

    def _build_mode_btn(mode_key: str) -> ft.Container:
        info = MODEL_REGISTRY[mode_key]
        downloaded = is_available(mode_key)
        selected = (_selected_mode[0] == mode_key)
        size_mb = info["size_mb"]
        size_str = f"{size_mb/1024:.1f}GB" if size_mb >= 1000 else f"{size_mb}MB"
        badge = ft.Container(
            content=ft.Text("✓" if downloaded else f"↓{size_str}", size=9,
                            color="#16A34A" if downloaded else "#D97706"),
            bgcolor="#DCFCE7" if downloaded else "#FEF3C7",
            border_radius=4,
            padding=ft.padding.symmetric(horizontal=4, vertical=1),
        )
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(f"{info['emoji']} {info['label']}", size=Typography.SMALL,
                                    weight=Typography.SEMI_BOLD, color=Colors.TEXT),
                            badge,
                        ],
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(info["description"], size=8, color=Colors.TEXT_MUTED),
                ],
                spacing=2,
            ),
            border=ft.border.all(1.5, Colors.PRIMARY if selected else Colors.BORDER),
            border_radius=Radius.MD,
            bgcolor="#EFF6FF" if selected else Colors.BG,
            padding=ft.padding.symmetric(horizontal=8, vertical=8),
            expand=True,
            on_click=lambda e, k=mode_key: _select_mode(k),
            ink=True,
        )

    mode_buttons_row = ft.Row(
        controls=[_build_mode_btn(k) for k in MODE_ORDER],
        spacing=Spacing.XS,
    )

    # 다운로드 영역 — 초기 상태를 미리 계산해 page.update() 없이 렌더링
    _init_mode = _selected_mode[0]
    _init_needs_dl = _init_mode in MODEL_REGISTRY and not is_available(_init_mode)
    _init_status_txt = ""
    if _init_needs_dl:
        _info0 = MODEL_REGISTRY[_init_mode]
        _sz = _info0["size_mb"]
        _init_status_txt = f"'{_info0['label']}' 모델 미다운로드 ({'%.1fGB' % (_sz/1024) if _sz>=1000 else f'{_sz}MB'})"

    _dl_status = ft.Text(_init_status_txt, size=Typography.SMALL, color=Colors.TEXT_MUTED)
    _dl_bar = ft.ProgressBar(value=0, visible=False, color=Colors.PRIMARY, bgcolor=Colors.BORDER)
    _dl_btn = ft.ElevatedButton(
        content=ft.Text("다운로드"), icon=ft.Icons.DOWNLOAD, visible=_init_needs_dl,
        style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=Colors.PRIMARY,
                             shape=ft.RoundedRectangleBorder(radius=Radius.MD)),
        on_click=lambda e: _start_download(),
    )
    _dl_cancel_btn = ft.OutlinedButton(
        content=ft.Text("취소"), visible=False,
        style=ft.ButtonStyle(color=Colors.ERROR,
                             shape=ft.RoundedRectangleBorder(radius=Radius.MD)),
        on_click=lambda e: _cancel_download(),
    )
    _dl_row = ft.Row(controls=[_dl_btn, _dl_cancel_btn], spacing=Spacing.SM)
    download_area = ft.Column(
        controls=[_dl_status, _dl_bar, _dl_row],
        spacing=4, visible=_init_needs_dl,
    )

    def _refresh_mode_buttons():
        mode_buttons_row.controls = [_build_mode_btn(k) for k in MODE_ORDER]
        if mode_buttons_row.page:
            mode_buttons_row.update()

    def _select_mode(key: str):
        _selected_mode[0] = key
        _refresh_mode_buttons()
        _update_download_area()

    def _update_download_area():
        mode = _selected_mode[0]
        if is_available(mode):
            download_area.visible = False
        else:
            info = MODEL_REGISTRY[mode]
            size_mb = info["size_mb"]
            size_str = f"{size_mb/1024:.1f}GB" if size_mb >= 1000 else f"{size_mb}MB"
            _dl_status.value = f"'{info['label']}' 모델 미다운로드 ({size_str})"
            _dl_btn.visible = True
            _dl_cancel_btn.visible = False
            _dl_bar.visible = False
            download_area.visible = True
        download_area.update()

    def _start_download():
        mode = _selected_mode[0]
        info = MODEL_REGISTRY[mode]
        cancel_ev = _threading.Event()
        _download_cancel[0] = cancel_ev
        _dl_btn.visible = False
        _dl_cancel_btn.visible = True
        _dl_bar.visible = True
        _dl_bar.value = 0
        _dl_status.value = "연결 중..."
        download_area.update()

        def _run():
            try:
                def on_progress(done, total):
                    if total:
                        async def _update_progress():
                            _dl_bar.value = done / total
                            _dl_status.value = f"다운로드 중... {done/1048576:.0f}/{total/1048576:.0f}MB"
                            _dl_bar.update()
                            _dl_status.update()
                        page.run_task(_update_progress)

                download_model(mode, on_progress=on_progress, cancel_event=cancel_ev)

                async def _on_done():
                    _dl_status.value = f"✅ '{info['label']}' 다운로드 완료!"
                    _dl_btn.visible = False
                    _dl_cancel_btn.visible = False
                    _dl_bar.visible = False
                    download_area.update()
                    _refresh_mode_buttons()
                page.run_task(_on_done)

            except DownloadCancelled:
                async def _on_cancel():
                    _dl_status.value = "다운로드가 취소되었습니다."
                    _dl_btn.visible = True
                    _dl_cancel_btn.visible = False
                    _dl_bar.visible = False
                    download_area.update()
                page.run_task(_on_cancel)

            except Exception as ex:
                async def _on_error():
                    _dl_status.value = f"❌ 다운로드 실패: {ex}"
                    _dl_btn.visible = True
                    _dl_cancel_btn.visible = False
                    _dl_bar.visible = False
                    download_area.update()
                page.run_task(_on_error)

        _threading.Thread(target=_run, daemon=True).start()

    def _cancel_download():
        if _download_cancel[0]:
            _download_cancel[0].set()

    # ── 전문가 모드 ──────────────────────────────────────
    stt_no_speech_field = ft.TextField(
        value=str(current_params.get("no_speech_thold", 0.4)),
        label="no_speech_thold (0.0~1.0)",
        hint_text="낮을수록 무음 억제 강도 증가 (기본: 0.4)",
        border_radius=Radius.MD, border_color=Colors.BORDER,
        focused_border_color=Colors.PRIMARY, text_size=Typography.BODY,
        label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
        dense=True,
    )
    stt_entropy_field = ft.TextField(
        value=str(current_params.get("entropy_thold", 2.4)),
        label="entropy_thold (0.0~5.0)",
        hint_text="반복/이상 출력 필터링 임계값 (기본: 2.4)",
        border_radius=Radius.MD, border_color=Colors.BORDER,
        focused_border_color=Colors.PRIMARY, text_size=Typography.BODY,
        label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
        dense=True,
    )
    stt_initial_prompt_field = ft.TextField(
        value=current_params.get("initial_prompt", "한국어 강의입니다."),
        label="initial_prompt",
        hint_text="모델에 전달할 초기 힌트 텍스트",
        border_radius=Radius.MD, border_color=Colors.BORDER,
        focused_border_color=Colors.PRIMARY, text_size=Typography.BODY,
        label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
        dense=True,
    )
    model_file_field = ft.TextField(
        hint_text="직접 다운로드한 .bin 파일 경로 (선택사항)",
        border_radius=Radius.MD, border_color=Colors.BORDER,
        focused_border_color=Colors.PRIMARY, text_size=Typography.BODY,
        label="커스텀 모델 파일",
        label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
        dense=True, expand=True,
    )
    if not hasattr(page, "_fp_model"):
        page._fp_model = ft.FilePicker()
        page.services.append(page._fp_model)
        page.update()
    model_file_picker = page._fp_model

    async def _browse_model(e):
        files = await model_file_picker.pick_files(
            dialog_title="whisper.cpp 모델 파일 선택 (.bin)",
            allowed_extensions=["bin"],
        )
        if files:
            model_file_field.value = files[0].path
            if model_file_field.page:
                model_file_field.update()

    expert_content = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.FOLDER_OPEN, size=14, color=Colors.TEXT_SECONDARY),
                        ft.Text("직접 모델 로드", size=Typography.CAPTION,
                                weight=Typography.SEMI_BOLD, color=Colors.TEXT_SECONDARY),
                    ],
                    spacing=Spacing.XS,
                ),
                ft.Row(
                    controls=[
                        model_file_field,
                        ft.OutlinedButton(
                            content=ft.Text("찾아보기"), icon=ft.Icons.FOLDER_OPEN,
                            on_click=_browse_model,
                            style=ft.ButtonStyle(color=Colors.PRIMARY,
                                                 shape=ft.RoundedRectangleBorder(radius=Radius.MD)),
                        ),
                    ],
                    spacing=Spacing.SM,
                ),
                ft.Text("파일 지정 시 모드 선택보다 우선합니다.", size=8, color=Colors.TEXT_MUTED),
                divider(),
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.TUNE, size=14, color=Colors.TEXT_SECONDARY),
                        ft.Text("파라미터 튜닝", size=Typography.CAPTION,
                                weight=Typography.SEMI_BOLD, color=Colors.TEXT_SECONDARY),
                    ],
                    spacing=Spacing.XS,
                ),
                stt_no_speech_field,
                stt_entropy_field,
                stt_initial_prompt_field,
            ],
            spacing=Spacing.SM,
        ),
        bgcolor="#F8FAFC", border_radius=Radius.MD,
        border=ft.border.all(1, Colors.BORDER),
        padding=ft.padding.all(Spacing.SM),
        visible=False,
    )

    expert_checkbox = ft.Checkbox(
        label="전문가 설정 (Expert Mode)",
        value=False, active_color=Colors.PRIMARY,
        on_change=lambda e: _toggle_expert(e.control.value),
    )

    def _toggle_expert(on: bool):
        expert_content.visible = on
        if expert_content.page:
            expert_content.update()

    whisper_section = ft.Column(
        controls=[
            ft.Text("모드 선택", size=Typography.CAPTION,
                    weight=Typography.SEMI_BOLD, color=Colors.TEXT_SECONDARY),
            mode_buttons_row,
            download_area,
            expert_checkbox,
            expert_content,
        ],
        spacing=Spacing.SM,
        visible=(current_stt == "whisper-cpp"),
    )

    def _on_stt_changed():
        engine = stt_dropdown.value or "whisper-cpp"
        is_whisper = (engine == "whisper-cpp")
        whisper_section.visible = is_whisper
        stt_api_key_field.visible = (engine == "returnzero")
        stt_description.value = _get_stt_description(engine)
        for ctrl in [whisper_section, stt_api_key_field, stt_description]:
            if ctrl.page:
                ctrl.update()

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
            whisper_section,
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
        chrome_path = (chrome_field.value or "").strip()

        # 요약 모드/분야 저장
        set_summary_mode(mode_dropdown.value or SummaryMode.NORMAL)
        set_subject_category(subject_dropdown.value or "자동 감지")
        set_subject_custom((subject_custom_field.value or "").strip())

        set_debug_mode(debug_switch.value)
        set_auto_open_folder(auto_open_switch.value)

        # STT 엔진 저장
        stt_engine = stt_dropdown.value or "whisper-cpp"
        set_stt_engine(stt_engine)
        if stt_engine == "returnzero":
            set_stt_api_key((stt_api_key_field.value or "").strip())
        if stt_engine == "whisper-cpp":
            # 커스텀 파일 경로 > 모드 선택
            custom_path = (model_file_field.value or "").strip()
            set_stt_model(custom_path if custom_path else _selected_mode[0])
            try:
                params = {
                    "no_speech_thold": float(stt_no_speech_field.value or 0.4),
                    "entropy_thold": float(stt_entropy_field.value or 2.4),
                    "initial_prompt": (stt_initial_prompt_field.value or "").strip() or None,
                }
                if params["initial_prompt"] is None:
                    del params["initial_prompt"]
                set_stt_params(params)
            except ValueError:
                pass

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
                        "요약 모드와 강의 분야를 선택하면 프롬프트가 자동 생성됩니다.",
                        size=Typography.SMALL,
                        color=Colors.TEXT_MUTED,
                    ),
                    mode_dropdown,
                    subject_dropdown,
                    subject_custom_field,
                    prompt_preview,
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
