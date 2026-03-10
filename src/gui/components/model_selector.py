"""
Flet 기반 AI 모델 선택기
"""

import flet as ft

from src.gui.theme import Colors, Typography, Radius

# 기본 모델 목록
_DEFAULT_MODELS = [
    ("gemini-2.5-flash", "Gemini 2.5 Flash (추천)"),
    ("gemini-2.5-pro", "Gemini 2.5 Pro"),
    ("gemini-2.5-flash-lite", "Gemini 2.5 Flash Lite"),
    ("gemini-2.0-flash", "Gemini 2.0 Flash"),
    ("gemini-2.0-flash-lite", "Gemini 2.0 Flash Lite"),
]

_CUSTOM_KEY = "__custom__"


class ModelSelector:
    """AI 모델 선택 드롭다운"""

    def __init__(self, on_change=None):
        self._on_change = on_change
        self._custom_input = ft.TextField(
            hint_text="모델명 직접 입력",
            border_radius=Radius.SM,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            text_size=Typography.BODY,
            visible=False,
            dense=True,
        )

        options = [ft.dropdown.Option(key=k, text=t) for k, t in _DEFAULT_MODELS]
        options.append(ft.dropdown.Option(key=_CUSTOM_KEY, text="직접 입력..."))

        self._dropdown = ft.Dropdown(
            options=options,
            value="gemini-2.5-flash",
            label="AI 모델",
            leading_icon=ft.Icons.SMART_TOY,
            border_radius=Radius.SM,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            text_size=Typography.BODY,
            label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            on_change=self._handle_change,
            dense=True,
        )

        self.control = ft.Column(
            controls=[self._dropdown, self._custom_input],
            spacing=4,
        )

    def _handle_change(self, e):
        is_custom = self._dropdown.value == _CUSTOM_KEY
        self._custom_input.visible = is_custom
        if self._custom_input.page:
            self._custom_input.update()
        if self._on_change:
            self._on_change(self.get_model())

    def get_model(self) -> str:
        if self._dropdown.value == _CUSTOM_KEY:
            return self._custom_input.value or "gemini-2.5-flash"
        return self._dropdown.value or "gemini-2.5-flash"

    def set_model(self, model_name: str):
        known_keys = [k for k, _ in _DEFAULT_MODELS]
        if model_name in known_keys:
            self._dropdown.value = model_name
            self._custom_input.visible = False
        else:
            self._dropdown.value = _CUSTOM_KEY
            self._custom_input.value = model_name
            self._custom_input.visible = True

    def set_enabled(self, enabled: bool):
        self._dropdown.disabled = not enabled
        self._custom_input.disabled = not enabled
