"""
Flet 기반 AI 엔진 + 모델 선택기
"""

import flet as ft

from src.gui.theme import Colors, Typography, Radius, Spacing
from src.summarize_pipeline.providers import ENGINE_REGISTRY, ClipboardProvider

# 엔진 드롭다운에 표시할 목록 (순서 유지)
_ENGINE_OPTIONS = [
    ("gemini", "Google Gemini"),
    ("openai", "OpenAI"),
    ("claude", "Anthropic Claude"),
    ("grok", "xAI Grok"),
    ("ollama", "Ollama (로컬 LLM, 무료)"),
    ("custom", "OpenAI 호환 (커스텀 엔드포인트)"),
    ("clipboard", "API 키 없이 사용"),
]

_CUSTOM_KEY = "__custom__"


class EngineModelSelector:
    """AI 엔진 + 모델 선택 드롭다운"""

    def __init__(self, on_engine_change=None, on_model_change=None):
        self._on_engine_change = on_engine_change
        self._on_model_change = on_model_change
        self._current_engine = "gemini"

        # 엔진 드롭다운
        engine_options = [
            ft.dropdown.Option(key=k, text=t) for k, t in _ENGINE_OPTIONS
        ]
        self._engine_dropdown = ft.Dropdown(
            options=engine_options,
            value="gemini",
            label="AI 엔진",
            leading_icon=ft.Icons.AUTO_AWESOME,
            border_radius=Radius.SM,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            text_size=Typography.BODY,
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            on_select=self._handle_engine_change,
            dense=True,
            tooltip="요약에 사용할 AI 엔진을 선택하세요",
        )

        # 모델 드롭다운
        self._model_dropdown = ft.Dropdown(
            options=[],
            value=None,
            label="AI 모델",
            leading_icon=ft.Icons.SMART_TOY,
            border_radius=Radius.SM,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            text_size=Typography.BODY,
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            on_select=self._handle_model_change,
            dense=True,
            tooltip="요약에 사용할 AI 모델을 선택하세요",
        )

        # 커스텀 모델 입력
        self._custom_input = ft.TextField(
            hint_text="모델명 직접 입력",
            border_radius=Radius.SM,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            text_size=Typography.BODY,
            visible=False,
            dense=True,
            tooltip="사용할 모델명을 직접 입력하세요 (예: gpt-4o)",
        )

        # 초기 모델 목록 채우기
        self._refresh_model_list()

        self.control = ft.Column(
            controls=[self._engine_dropdown, self._model_dropdown, self._custom_input],
            spacing=Spacing.SM,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _get_models_for_engine(self, engine: str) -> list[tuple[str, str]]:
        """엔진에 해당하는 모델 목록 반환"""
        if engine == "clipboard":
            return ClipboardProvider.available_models()
        cls = ENGINE_REGISTRY.get(engine)
        if cls:
            return cls.available_models()
        return []

    def _refresh_model_list(self):
        """현재 선택된 엔진에 맞게 모델 드롭다운 갱신"""
        models = self._get_models_for_engine(self._current_engine)
        options = [ft.dropdown.Option(key=k, text=t) for k, t in models]
        options.append(ft.dropdown.Option(key=_CUSTOM_KEY, text="직접 입력..."))

        self._model_dropdown.options = options
        if models:
            self._model_dropdown.value = models[0][0]
        else:
            self._model_dropdown.value = None

        self._custom_input.visible = False

    def _handle_engine_change(self, e):
        self._current_engine = self._engine_dropdown.value or "gemini"
        self._refresh_model_list()

        # UI 업데이트
        if self._model_dropdown.page:
            self._model_dropdown.update()
        if self._custom_input.page:
            self._custom_input.update()

        if self._on_engine_change:
            self._on_engine_change(self._current_engine)

    def _handle_model_change(self, e):
        is_custom = self._model_dropdown.value == _CUSTOM_KEY
        self._custom_input.visible = is_custom
        if self._custom_input.page:
            self._custom_input.update()
        if self._on_model_change:
            self._on_model_change(self.get_model())

    def get_engine(self) -> str:
        """현재 선택된 엔진 반환"""
        return self._current_engine

    def get_model(self) -> str:
        """현재 선택된 모델명 반환"""
        if self._model_dropdown.value == _CUSTOM_KEY:
            custom = self._custom_input.value or ""
            if custom.strip():
                return custom.strip()
            # 커스텀 입력이 비어있으면 기본 모델
            models = self._get_models_for_engine(self._current_engine)
            return models[0][0] if models else ""
        return self._model_dropdown.value or ""

    def set_engine(self, engine: str):
        """엔진 설정"""
        known_engines = [k for k, _ in _ENGINE_OPTIONS]
        if engine in known_engines:
            self._current_engine = engine
            self._engine_dropdown.value = engine
            self._refresh_model_list()

    def set_model(self, model_name: str):
        """모델 설정"""
        models = self._get_models_for_engine(self._current_engine)
        known_keys = [k for k, _ in models]
        if model_name in known_keys:
            self._model_dropdown.value = model_name
            self._custom_input.visible = False
        else:
            self._model_dropdown.value = _CUSTOM_KEY
            self._custom_input.value = model_name
            self._custom_input.visible = True

    def set_enabled(self, enabled: bool):
        """활성/비활성 전환"""
        self._engine_dropdown.disabled = not enabled
        self._model_dropdown.disabled = not enabled
        self._custom_input.disabled = not enabled


# 하위 호환을 위한 별칭
ModelSelector = EngineModelSelector
