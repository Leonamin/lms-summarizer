"""
STT 설정 섹션 — 좌측 패널 배치용, 접기/펼치기 지원
"""

import threading
import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.gui.core.file_manager import (
    get_stt_engine, set_stt_engine,
    get_stt_model, set_stt_model,
    get_stt_params, set_stt_params,
    get_stt_api_key, set_stt_api_key,
)

_STT_ENGINE_OPTIONS = [
    ("whisper-cpp", "whisper-cpp (로컬, 무료)"),
    ("faster-whisper", "faster-whisper (로컬, GPU 지원)"),
    ("returnzero", "ReturnZero API (유료)"),
]


class STTSettingsSection:
    """STT 설정 섹션 (접기/펼치기)"""

    def __init__(self, page: ft.Page):
        self._page = page
        self._expanded = True

        from src.audio_pipeline.model_manager import (
            MODEL_REGISTRY, MODE_ORDER, is_available, download_model, DownloadCancelled,
            FW_MODEL_REGISTRY, FW_MODE_ORDER,
        )
        self._MODEL_REGISTRY = MODEL_REGISTRY
        self._MODE_ORDER = MODE_ORDER
        self._is_available = is_available
        self._download_model = download_model
        self._DownloadCancelled = DownloadCancelled

        current_model = get_stt_model()
        self._selected_mode = [current_model if current_model in MODE_ORDER else MODE_ORDER[0]]
        self._fw_selected_mode = [current_model if current_model in FW_MODE_ORDER else FW_MODE_ORDER[0]]
        self._download_cancel: list = [None]

        # ── 헤더 ─────────────────────────────────────────
        self._summary = ft.Text(
            self._get_summary_text(),
            size=Typography.SMALL,
            color=Colors.TEXT_MUTED,
            visible=False,
        )
        self._chevron = ft.Icon(ft.Icons.EXPAND_LESS, size=16, color=Colors.TEXT_SECONDARY)

        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.MIC, size=13, color=Colors.TEXT_MUTED),
                    ft.Text(
                        "STT 설정",
                        size=Typography.SMALL,
                        weight=Typography.SEMI_BOLD,
                        color=Colors.TEXT_MUTED,
                        expand=True,
                    ),
                    self._chevron,
                ],
                spacing=Spacing.XS,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            on_click=self._toggle,
            ink=True,
            border_radius=Radius.SM,
        )

        # ── 모드 버튼 ─────────────────────────────────────
        self._mode_row = ft.Row(
            controls=self._build_mode_buttons(),
            spacing=Spacing.XS,
        )

        # ── 다운로드 영역 ──────────────────────────────────
        init_mode = self._selected_mode[0]
        init_needs_dl = init_mode in MODEL_REGISTRY and not is_available(init_mode)
        init_status = ""
        if init_needs_dl:
            _info = MODEL_REGISTRY[init_mode]
            _sz = _info["size_mb"]
            init_status = f"'{_info['label']}' 미다운로드 ({'%.1fGB' % (_sz/1024) if _sz >= 1000 else f'{_sz}MB'})"

        self._dl_status = ft.Text(init_status, size=Typography.SMALL, color=Colors.TEXT_MUTED)
        self._dl_bar = ft.ProgressBar(value=0, visible=False, color=Colors.PRIMARY, bgcolor=Colors.BORDER)
        self._dl_btn = ft.ElevatedButton(
            content=ft.Text("다운로드"), icon=ft.Icons.DOWNLOAD, visible=init_needs_dl,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE, bgcolor=Colors.PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
            ),
            on_click=lambda e: self._start_download(),
        )
        self._dl_cancel_btn = ft.OutlinedButton(
            content=ft.Text("취소"), visible=False,
            style=ft.ButtonStyle(
                color=Colors.ERROR,
                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
            ),
            on_click=lambda e: self._cancel_download(),
        )
        self._download_area = ft.Column(
            controls=[
                self._dl_status,
                self._dl_bar,
                ft.Row(controls=[self._dl_btn, self._dl_cancel_btn], spacing=Spacing.SM),
            ],
            spacing=4,
            visible=init_needs_dl,
        )

        # ── 전문가 설정 (접기/펼치기) ──────────────────────
        self._expert_expanded = False
        self._expert_chevron = ft.Icon(ft.Icons.EXPAND_MORE, size=14, color=Colors.TEXT_SECONDARY)
        current_params = get_stt_params()
        current_stt = get_stt_engine()
        self._no_speech_field = ft.TextField(
            value=str(current_params.get("no_speech_thold", 0.4)),
            label="no_speech_thold (0.0~1.0)",
            hint_text="낮을수록 무음 억제 강도 증가 (기본: 0.4)",
            border_radius=Radius.SM, border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY, text_size=Typography.SMALL,
            label_style=ft.TextStyle(size=9, color=Colors.TEXT_SECONDARY),
            dense=True,
            tooltip="무음 구간 감지 민감도 — 낮을수록 더 적극적으로 무음을 제거합니다",
        )
        self._entropy_field = ft.TextField(
            value=str(current_params.get("entropy_thold", 2.4)),
            label="entropy_thold (0.0~5.0)",
            hint_text="반복/이상 출력 필터링 (기본: 2.4)",
            border_radius=Radius.SM, border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY, text_size=Typography.SMALL,
            label_style=ft.TextStyle(size=9, color=Colors.TEXT_SECONDARY),
            dense=True,
            tooltip="높을수록 반복/이상 텍스트 허용 — 낮추면 필터링이 강해집니다",
        )
        self._initial_prompt_field = ft.TextField(
            value=current_params.get("initial_prompt", "한국어 강의입니다."),
            label="initial_prompt",
            hint_text="모델 초기 힌트 텍스트",
            border_radius=Radius.SM, border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY, text_size=Typography.SMALL,
            label_style=ft.TextStyle(size=9, color=Colors.TEXT_SECONDARY),
            dense=True,
            tooltip="Whisper 모델에 전달되는 초기 힌트 텍스트 — 인식 언어와 맥락을 안내합니다",
        )
        self._repeat_threshold_field = ft.TextField(
            value=str(current_params.get("repeat_threshold", 4)),
            label="반복 제거 임계값 (0 = 비활성화)",
            hint_text="같은 구문이 N회 이상 연속되면 1개로 축약 (기본: 4)",
            border_radius=Radius.SM, border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY, text_size=Typography.SMALL,
            label_style=ft.TextStyle(size=9, color=Colors.TEXT_SECONDARY),
            dense=True,
            tooltip="같은 구문이 이 횟수 이상 연속되면 1개로 축약합니다 (0이면 비활성화)",
        )
        self._device_dd = ft.Dropdown(
            options=[
                ft.dropdown.Option(key="auto", text="자동 감지 (권장)"),
                ft.dropdown.Option(key="cuda", text="CUDA (NVIDIA GPU)"),
                ft.dropdown.Option(key="cpu", text="CPU"),
            ],
            value=current_params.get("device", "auto"),
            label="장치 선택",
            border_radius=Radius.SM,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            text_size=Typography.BODY,
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            dense=True,
            tooltip="faster-whisper 전용: 추론에 사용할 장치 선택",
            visible=(current_stt == "faster-whisper"),
        )
        self._expert_content = ft.Column(
            controls=[self._no_speech_field, self._entropy_field, self._initial_prompt_field, self._repeat_threshold_field, self._device_dd],
            spacing=Spacing.SM,
            visible=False,
        )
        expert_header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.TUNE, size=12, color=Colors.TEXT_SECONDARY),
                    ft.Text(
                        "전문가 설정",
                        size=Typography.SMALL,
                        color=Colors.TEXT_SECONDARY,
                        expand=True,
                    ),
                    self._expert_chevron,
                ],
                spacing=Spacing.XS,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            on_click=self._toggle_expert,
            padding=ft.padding.symmetric(vertical=4),
            ink=True,
            border_radius=Radius.SM,
        )

        # ── Whisper 전용 섹션 ──────────────────────────────
        self._whisper_section = ft.Column(
            controls=[
                ft.Text(
                    "모드 선택",
                    size=9,
                    color=Colors.TEXT_SECONDARY,
                    weight=Typography.SEMI_BOLD,
                ),
                self._mode_row,
                self._download_area,
                ft.Divider(height=1, color=Colors.BORDER),
                expert_header,
                self._expert_content,
            ],
            spacing=Spacing.SM,
            visible=(current_stt == "whisper-cpp"),
        )

        # ── Faster-Whisper 전용 섹션 ───────────────────────
        self._fw_mode_row = ft.Row(
            controls=self._build_fw_mode_buttons(),
            spacing=Spacing.XS,
        )
        self._fw_section = ft.Column(
            controls=[
                ft.Text(
                    "모드 선택",
                    size=9,
                    color=Colors.TEXT_SECONDARY,
                    weight=Typography.SEMI_BOLD,
                ),
                self._fw_mode_row,
            ],
            spacing=Spacing.SM,
            visible=(current_stt == "faster-whisper"),
        )

        # ── ReturnZero API 키 ──────────────────────────────
        self._rtzr_api_field = ft.TextField(
            value=get_stt_api_key(),
            hint_text="client_id:client_secret",
            border_radius=Radius.SM, border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY, text_size=Typography.BODY,
            label="ReturnZero API 키",
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            prefix_icon=ft.Icons.KEY,
            visible=(current_stt == "returnzero"),
            dense=True,
            tooltip="ReturnZero API 키를 client_id:client_secret 형식으로 입력하세요",
        )

        # ── 엔진 드롭다운 ──────────────────────────────────
        self._engine_dd = ft.Dropdown(
            options=[ft.dropdown.Option(key=k, text=t) for k, t in _STT_ENGINE_OPTIONS],
            value=current_stt,
            label="STT 엔진",
            leading_icon=ft.Icons.MIC,
            border_radius=Radius.SM,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            text_size=Typography.BODY,
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            on_select=self._on_engine_changed,
            dense=True,
            tooltip="음성 인식(STT)에 사용할 엔진을 선택하세요",
        )

        # ── 적용 버튼 ─────────────────────────────────────
        self._save_btn = ft.TextButton(
            content=ft.Text("적용", size=Typography.SMALL),
            icon=ft.Icons.CHECK,
            on_click=self._save,
            style=ft.ButtonStyle(color=Colors.PRIMARY),
        )

        # ── 펼쳐진 콘텐츠 전체 ─────────────────────────────
        self._expanded_content = ft.Column(
            controls=[
                self._engine_dd,
                self._whisper_section,
                self._fw_section,
                self._rtzr_api_field,
                self._save_btn,
            ],
            spacing=Spacing.SM,
            visible=True,
        )

        self.control = ft.Column(
            controls=[header, self._summary, self._expanded_content],
            spacing=Spacing.XS,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    # ── 내부 헬퍼 ─────────────────────────────────────────

    def _get_summary_text(self) -> str:
        engine = get_stt_engine()
        if engine == "returnzero":
            return "ReturnZero API"
        if engine == "faster-whisper":
            model = get_stt_model()
            from src.audio_pipeline.model_manager import FW_MODEL_REGISTRY
            info = FW_MODEL_REGISTRY.get(model)
            label = info["label"] if info else model
            device = get_stt_params().get("device", "auto")
            return f"faster-whisper · {label} · {device}"
        model = get_stt_model()
        from src.audio_pipeline.model_manager import MODEL_REGISTRY
        info = MODEL_REGISTRY.get(model)
        label = info["label"] if info else model
        return f"whisper-cpp · {label}"

    def _build_mode_buttons(self) -> list:
        buttons = []
        for mode_key in self._MODE_ORDER:
            info = self._MODEL_REGISTRY[mode_key]
            downloaded = self._is_available(mode_key)
            selected = (self._selected_mode[0] == mode_key)
            size_mb = info["size_mb"]
            size_str = f"{size_mb/1024:.1f}GB" if size_mb >= 1000 else f"{size_mb}MB"
            badge = ft.Container(
                content=ft.Text(
                    "✓" if downloaded else f"↓{size_str}",
                    size=8,
                    color="#16A34A" if downloaded else "#D97706",
                ),
                bgcolor="#DCFCE7" if downloaded else "#FEF3C7",
                border_radius=3,
                padding=ft.padding.symmetric(horizontal=3, vertical=1),
            )
            btn = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(
                                    f"{info['emoji']} {info['label']}",
                                    size=Typography.SMALL,
                                    weight=Typography.SEMI_BOLD,
                                    color=Colors.TEXT,
                                ),
                                badge,
                            ],
                            spacing=3,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text(info["description"], size=8, color=Colors.TEXT_MUTED),
                    ],
                    spacing=2,
                ),
                border=ft.border.all(1.5, Colors.PRIMARY if selected else Colors.BORDER),
                border_radius=Radius.SM,
                bgcolor="#EFF6FF" if selected else Colors.BG,
                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                expand=True,
                on_click=lambda e, k=mode_key: self._select_mode(k),
                ink=True,
            )
            buttons.append(btn)
        return buttons

    def _build_fw_mode_buttons(self) -> list:
        from src.audio_pipeline.model_manager import FW_MODEL_REGISTRY, FW_MODE_ORDER
        buttons = []
        for mode_key in FW_MODE_ORDER:
            info = FW_MODEL_REGISTRY[mode_key]
            selected = (self._fw_selected_mode[0] == mode_key)
            size_mb = info["size_mb"]
            size_str = f"{size_mb/1024:.1f}GB" if size_mb >= 1000 else f"{size_mb}MB"
            badge = ft.Container(
                content=ft.Text(f"↓{size_str}", size=8, color="#D97706"),
                bgcolor="#FEF3C7", border_radius=3,
                padding=ft.padding.symmetric(horizontal=3, vertical=1),
            )
            btn = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(
                                    f"{info['emoji']} {info['label']}",
                                    size=Typography.SMALL,
                                    weight=Typography.SEMI_BOLD,
                                    color=Colors.TEXT,
                                ),
                                badge,
                            ],
                            spacing=3,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text(info["description"], size=8, color=Colors.TEXT_MUTED),
                    ],
                    spacing=2,
                ),
                border=ft.border.all(1.5, Colors.PRIMARY if selected else Colors.BORDER),
                border_radius=Radius.SM,
                bgcolor="#EFF6FF" if selected else Colors.BG,
                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                expand=True,
                on_click=lambda e, k=mode_key: self._select_fw_mode(k),
                ink=True,
            )
            buttons.append(btn)
        return buttons

    def _select_fw_mode(self, key: str):
        self._fw_selected_mode[0] = key
        self._fw_mode_row.controls = self._build_fw_mode_buttons()
        try:
            if self._fw_mode_row.page:
                self._fw_mode_row.update()
        except Exception:
            pass

    def _refresh_mode_buttons(self):
        self._mode_row.controls = self._build_mode_buttons()
        try:
            if self._mode_row.page:
                self._mode_row.update()
        except Exception:
            pass

    def _select_mode(self, key: str):
        self._selected_mode[0] = key
        self._refresh_mode_buttons()
        self._update_download_area()

    def _update_download_area(self):
        mode = self._selected_mode[0]
        if self._is_available(mode):
            self._download_area.visible = False
        else:
            info = self._MODEL_REGISTRY[mode]
            size_mb = info["size_mb"]
            size_str = f"{size_mb/1024:.1f}GB" if size_mb >= 1000 else f"{size_mb}MB"
            self._dl_status.value = f"'{info['label']}' 미다운로드 ({size_str})"
            self._dl_btn.visible = True
            self._dl_cancel_btn.visible = False
            self._dl_bar.visible = False
            self._download_area.visible = True
        try:
            if self._download_area.page:
                self._download_area.update()
        except Exception:
            pass

    def _start_download(self):
        mode = self._selected_mode[0]
        info = self._MODEL_REGISTRY[mode]
        cancel_ev = threading.Event()
        self._download_cancel[0] = cancel_ev
        self._dl_btn.visible = False
        self._dl_cancel_btn.visible = True
        self._dl_bar.visible = True
        self._dl_bar.value = 0
        self._dl_status.value = "연결 중..."
        self._download_area.update()

        def _run():
            try:
                def on_progress(done, total):
                    if total:
                        async def _upd():
                            self._dl_bar.value = done / total
                            self._dl_status.value = f"다운로드 중... {done/1048576:.0f}/{total/1048576:.0f}MB"
                            self._dl_bar.update()
                            self._dl_status.update()
                        self._page.run_task(_upd)

                self._download_model(mode, on_progress=on_progress, cancel_event=cancel_ev)

                async def _on_done():
                    self._dl_status.value = f"✅ '{info['label']}' 다운로드 완료!"
                    self._dl_btn.visible = False
                    self._dl_cancel_btn.visible = False
                    self._dl_bar.visible = False
                    self._download_area.update()
                    self._refresh_mode_buttons()
                self._page.run_task(_on_done)

            except self._DownloadCancelled:
                async def _on_cancel():
                    self._dl_status.value = "다운로드 취소됨"
                    self._dl_btn.visible = True
                    self._dl_cancel_btn.visible = False
                    self._dl_bar.visible = False
                    self._download_area.update()
                self._page.run_task(_on_cancel)

            except Exception as ex:
                async def _on_error():
                    self._dl_status.value = f"❌ 다운로드 실패: {ex}"
                    self._dl_btn.visible = True
                    self._dl_cancel_btn.visible = False
                    self._dl_bar.visible = False
                    self._download_area.update()
                self._page.run_task(_on_error)

        threading.Thread(target=_run, daemon=True).start()

    def _cancel_download(self):
        if self._download_cancel[0]:
            self._download_cancel[0].set()

    def _toggle_expert(self, e):
        self._expert_expanded = not self._expert_expanded
        self._expert_content.visible = self._expert_expanded
        self._expert_chevron.icon = (
            ft.Icons.EXPAND_LESS if self._expert_expanded else ft.Icons.EXPAND_MORE
        )
        self._expert_content.update()
        self._expert_chevron.update()

    def _on_engine_changed(self, e):
        engine = self._engine_dd.value or "whisper-cpp"
        self._whisper_section.visible = (engine == "whisper-cpp")
        self._fw_section.visible = (engine == "faster-whisper")
        self._rtzr_api_field.visible = (engine == "returnzero")
        self._device_dd.visible = (engine == "faster-whisper")
        self._whisper_section.update()
        self._fw_section.update()
        self._rtzr_api_field.update()
        self._device_dd.update()
        self._summary.value = self._get_summary_text()
        try:
            if self._summary.page:
                self._summary.update()
        except Exception:
            pass

    def _save(self, e):
        engine = self._engine_dd.value or "whisper-cpp"
        set_stt_engine(engine)
        if engine == "returnzero":
            set_stt_api_key((self._rtzr_api_field.value or "").strip())
        if engine == "whisper-cpp":
            set_stt_model(self._selected_mode[0])
            try:
                params = {
                    "no_speech_thold": float(self._no_speech_field.value or 0.4),
                    "entropy_thold": float(self._entropy_field.value or 2.4),
                    "initial_prompt": (self._initial_prompt_field.value or "").strip() or None,
                    "repeat_threshold": int(float(self._repeat_threshold_field.value or 4)),
                }
                if params["initial_prompt"] is None:
                    del params["initial_prompt"]
                set_stt_params(params)
            except ValueError:
                pass
        elif engine == "faster-whisper":
            set_stt_model(self._fw_selected_mode[0])
            try:
                params = {
                    "device": self._device_dd.value or "auto",
                    "vad_filter": True,
                    "initial_prompt": (self._initial_prompt_field.value or "").strip() or None,
                    "repeat_threshold": int(float(self._repeat_threshold_field.value or 4)),
                }
                if params["initial_prompt"] is None:
                    del params["initial_prompt"]
                set_stt_params(params)
            except ValueError:
                pass
        self._summary.value = self._get_summary_text()
        try:
            if self._summary.page:
                self._summary.update()
        except Exception:
            pass

    def _toggle(self, e):
        self._expanded = not self._expanded
        self._expanded_content.visible = self._expanded
        self._summary.visible = not self._expanded
        if not self._expanded:
            self._summary.value = self._get_summary_text()
        self._chevron.icon = (
            ft.Icons.EXPAND_LESS if self._expanded else ft.Icons.EXPAND_MORE
        )
        self._expanded_content.update()
        self._summary.update()
        self._chevron.update()

    # ── Public API ─────────────────────────────────────────

    def set_enabled(self, enabled: bool):
        self._engine_dd.disabled = not enabled
        self._dl_btn.disabled = not enabled
        self._save_btn.disabled = not enabled
