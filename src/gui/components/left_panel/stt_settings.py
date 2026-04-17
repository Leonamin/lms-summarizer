"""
STT 설정 섹션 — 좌측 패널 배치용, 접기/펼치기 지원
"""

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.gui.core.file_manager import (
    get_stt_engine, set_stt_engine,
    get_stt_model, set_stt_model,
    get_stt_params, set_stt_params,
    get_stt_api_key, set_stt_api_key,
)

_STT_ENGINE_OPTIONS = [
    ("faster-whisper", "faster-whisper (로컬, GPU 지원)"),
    ("openai-compatible", "OpenAI 호환 엔드포인트 (로컬 서버)"),
    ("openai-whisper", "OpenAI Whisper API (클라우드, $0.006/분)"),
    ("returnzero", "ReturnZero API (유료)"),
]


class STTSettingsSection:
    """STT 설정 섹션 (접기/펼치기)"""

    def __init__(self, page: ft.Page):
        self._page = page
        self._expanded = True

        from src.audio_pipeline.model_manager import FW_MODEL_REGISTRY, FW_MODE_ORDER
        self._FW_MODEL_REGISTRY = FW_MODEL_REGISTRY
        self._FW_MODE_ORDER = FW_MODE_ORDER

        current_model = get_stt_model()
        self._fw_selected_mode = [current_model if current_model in FW_MODE_ORDER else FW_MODE_ORDER[0]]

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

        current_params = get_stt_params()
        current_stt = get_stt_engine()

        # ── 전문가 설정 ────────────────────────────────────
        self._expert_expanded = False
        self._expert_chevron = ft.Icon(ft.Icons.EXPAND_MORE, size=14, color=Colors.TEXT_SECONDARY)
        self._initial_prompt_field = ft.TextField(
            value=current_params.get("initial_prompt", "한국어 강의입니다."),
            label="initial_prompt",
            hint_text="모델 초기 힌트 텍스트",
            border_radius=Radius.SM, border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY, text_size=Typography.SMALL,
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            dense=True,
            tooltip="Whisper 모델에 전달되는 초기 힌트 텍스트 — 인식 언어와 맥락을 안내합니다",
        )
        self._repeat_threshold_field = ft.TextField(
            value=str(current_params.get("repeat_threshold", 4)),
            label="반복 제거 임계값 (0 = 비활성화)",
            hint_text="같은 구문이 N회 이상 연속되면 1개로 축약 (기본: 4)",
            border_radius=Radius.SM, border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY, text_size=Typography.SMALL,
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
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
            tooltip="추론에 사용할 장치 선택",
        )
        self._expert_content = ft.Column(
            controls=[self._initial_prompt_field, self._repeat_threshold_field, self._device_dd],
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

        # ── Faster-Whisper 섹션 ────────────────────────────
        self._fw_mode_row = ft.Row(
            controls=self._build_fw_mode_buttons(),
            spacing=Spacing.XS,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            intrinsic_height=True,
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
                ft.Divider(height=1, color=Colors.BORDER),
                expert_header,
                self._expert_content,
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

        # ── OpenAI Whisper API 키 ──────────────────────────
        self._openai_stt_key_field = ft.TextField(
            value=get_stt_api_key(engine="openai-whisper"),
            hint_text="sk-...",
            border_radius=Radius.SM, border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY, text_size=Typography.BODY,
            label="OpenAI API 키",
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            prefix_icon=ft.Icons.KEY,
            visible=(current_stt == "openai-whisper"),
            dense=True,
            password=True,
            can_reveal_password=True,
            tooltip="OpenAI Whisper API에 사용할 API 키를 입력하세요",
        )

        # ── OpenAI Whisper 안내 ────────────────────────────
        self._openai_whisper_notice = ft.Container(
            content=ft.Text(
                "클라우드 STT — 로컬 모델 다운로드 없이 빠른 음성 인식\n"
                "요금: $0.006/분 (OpenAI 계정 필요)",
                size=Typography.SMALL,
                color="#1D4ED8",
            ),
            bgcolor="#EFF6FF",
            border=ft.border.all(1, "#BFDBFE"),
            border_radius=Radius.SM,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            visible=(current_stt == "openai-whisper"),
        )

        # ── OpenAI Compatible STT (엔드포인트 URL + 선택적 API 키) ──
        self._compat_stt_url_field = ft.TextField(
            value=get_stt_api_key(engine="openai-compatible-base-url"),
            hint_text="http://localhost:8765/aio/v1/stt",
            border_radius=Radius.SM, border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY, text_size=Typography.BODY,
            label="STT 엔드포인트 URL",
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            prefix_icon=ft.Icons.LINK,
            visible=(current_stt == "openai-compatible"),
            dense=True,
            tooltip="OpenAI 호환 STT 서버 URL (예: http://localhost:8765/aio/v1/stt)",
        )
        self._compat_stt_model_field = ft.TextField(
            value=get_stt_api_key(engine="openai-compatible-model"),
            hint_text="Systran/faster-whisper-small",
            border_radius=Radius.SM, border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY, text_size=Typography.BODY,
            label="STT 모델명",
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            prefix_icon=ft.Icons.MODEL_TRAINING,
            visible=(current_stt == "openai-compatible"),
            dense=True,
            tooltip="서버에서 사용할 모델명 (예: Systran/faster-whisper-small, Systran/faster-whisper-large-v3)",
        )
        self._compat_stt_key_field = ft.TextField(
            value=get_stt_api_key(engine="openai-compatible"),
            hint_text="선택사항 — 비워두면 인증 없이 전송",
            border_radius=Radius.SM, border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY, text_size=Typography.BODY,
            label="API 키 (선택사항)",
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            prefix_icon=ft.Icons.KEY,
            visible=(current_stt == "openai-compatible"),
            dense=True,
            password=True,
            can_reveal_password=True,
            tooltip="인증이 필요한 서버인 경우만 입력하세요",
        )
        self._compat_stt_notice = ft.Container(
            content=ft.Text(
                "로컬/원격 OpenAI 호환 STT 서버에 연결합니다.\n"
                "Speaches, faster-whisper-server, LM Studio 등을 사용할 수 있습니다.",
                size=Typography.SMALL,
                color="#7C3AED",  # violet-600
            ),
            bgcolor="#F5F3FF",  # violet-50
            border=ft.border.all(1, "#DDD6FE"),  # violet-200
            border_radius=Radius.SM,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            visible=(current_stt == "openai-compatible"),
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
                self._fw_section,
                self._openai_whisper_notice,
                self._openai_stt_key_field,
                self._compat_stt_notice,
                self._compat_stt_url_field,
                self._compat_stt_model_field,
                self._compat_stt_key_field,
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
        if engine == "openai-whisper":
            return "OpenAI Whisper API (클라우드)"
        if engine == "openai-compatible":
            url = get_stt_api_key(engine="openai-compatible-base-url")
            model = get_stt_api_key(engine="openai-compatible-model") or "faster-whisper-small"
            short_url = url.replace("http://", "").replace("https://", "") if url else "미설정"
            return f"OpenAI 호환 · {short_url} · {model}"
        model = get_stt_model()
        from src.audio_pipeline.model_manager import FW_MODEL_REGISTRY
        info = FW_MODEL_REGISTRY.get(model)
        label = info["label"] if info else model
        device = get_stt_params().get("device", "auto")
        return f"faster-whisper · {label} · {device}"

    def _build_fw_mode_buttons(self) -> list:
        buttons = []
        for mode_key in self._FW_MODE_ORDER:
            info = self._FW_MODEL_REGISTRY[mode_key]
            selected = (self._fw_selected_mode[0] == mode_key)
            size_mb = info["size_mb"]
            size_str = f"{size_mb/1024:.1f}GB" if size_mb >= 1000 else f"{size_mb}MB"
            tooltip_text = f"{info['description']}\n모델 크기: {size_str}"
            btn = ft.Container(
                content=ft.Text(
                    f"{info['emoji']} {info['label']}",
                    size=Typography.SMALL,
                    weight=Typography.SEMI_BOLD,
                    color=Colors.TEXT,
                    text_align=ft.TextAlign.CENTER,
                ),
                border=ft.border.all(1.5, Colors.PRIMARY if selected else Colors.BORDER),
                border_radius=Radius.SM,
                bgcolor="#EFF6FF" if selected else Colors.BG,
                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                expand=True,
                on_click=lambda e, k=mode_key: self._select_fw_mode(k),
                ink=True,
                tooltip=tooltip_text,
                alignment=ft.Alignment.CENTER,
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

    def _toggle_expert(self, e):
        self._expert_expanded = not self._expert_expanded
        self._expert_content.visible = self._expert_expanded
        self._expert_chevron.icon = (
            ft.Icons.EXPAND_LESS if self._expert_expanded else ft.Icons.EXPAND_MORE
        )
        self._expert_content.update()
        self._expert_chevron.update()

    def _on_engine_changed(self, e):
        engine = self._engine_dd.value or "faster-whisper"
        self._fw_section.visible = (engine == "faster-whisper")
        self._rtzr_api_field.visible = (engine == "returnzero")
        self._openai_stt_key_field.visible = (engine == "openai-whisper")
        self._openai_whisper_notice.visible = (engine == "openai-whisper")
        # OpenAI Compatible STT 섹션 토글
        is_compat = (engine == "openai-compatible")
        self._compat_stt_notice.visible = is_compat
        self._compat_stt_url_field.visible = is_compat
        self._compat_stt_model_field.visible = is_compat
        self._compat_stt_key_field.visible = is_compat
        # 업데이트
        for ctrl in [
            self._fw_section, self._rtzr_api_field,
            self._openai_stt_key_field, self._openai_whisper_notice,
            self._compat_stt_notice, self._compat_stt_url_field,
            self._compat_stt_model_field, self._compat_stt_key_field,
        ]:
            try:
                ctrl.update()
            except Exception:
                pass
        self._summary.value = self._get_summary_text()
        try:
            if self._summary.page:
                self._summary.update()
        except Exception:
            pass

    def _save(self, e):
        engine = self._engine_dd.value or "faster-whisper"
        set_stt_engine(engine)
        if engine == "returnzero":
            set_stt_api_key((self._rtzr_api_field.value or "").strip())
        elif engine == "openai-whisper":
            set_stt_api_key((self._openai_stt_key_field.value or "").strip(), engine="openai-whisper")
            # openai-whisper STT 파라미터에 API 키 전달
            params = get_stt_params()
            params["api_key"] = (self._openai_stt_key_field.value or "").strip()
            set_stt_params(params)
        elif engine == "openai-compatible":
            base_url = (self._compat_stt_url_field.value or "").strip()
            model_name = (self._compat_stt_model_field.value or "").strip() or "Systran/faster-whisper-small"
            api_key = (self._compat_stt_key_field.value or "").strip()
            # base_url과 model을 stt_api_keys에 저장 (전용 키 사용)
            set_stt_api_key(base_url, engine="openai-compatible-base-url")
            set_stt_api_key(model_name, engine="openai-compatible-model")
            set_stt_api_key(api_key, engine="openai-compatible")
            # 파라미터에도 주입 (transcriber가 읽도록)
            params = get_stt_params()
            params["base_url"] = base_url
            params["api_key"] = api_key
            set_stt_params(params)
            # stt_model에도 모델명 저장 (UI에 표시용)
            set_stt_model(model_name)
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
        self._save_btn.disabled = not enabled
