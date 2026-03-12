"""
AI 설정 섹션 - 엔진/모델 선택 + API 키 입력
"""

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.gui.config.settings import INPUT_FIELD_CONFIGS
from src.gui.components.input_field import InputField
from src.gui.components.model_selector import EngineModelSelector
from src.gui.core.file_manager import get_api_key_for_engine


_ENGINE_LABELS = {
    "gemini": "Gemini API 키",
    "openai": "OpenAI API 키",
    "claude": "Anthropic API 키",
    "grok": "xAI API 키",
    "clipboard": "API 키 (불필요)",
}


class AISettingsSection:
    """AI 엔진 + 모델 + API 키 통합 섹션"""

    def __init__(self, on_engine_change=None):
        self._external_engine_cb = on_engine_change

        self._api_field = InputField(INPUT_FIELD_CONFIGS['api_key'])
        self._model_selector = EngineModelSelector(
            on_engine_change=self._handle_engine_change,
        )

        # 클립보드 모드 안내 (HTML: bg-amber-50 border-amber-200)
        self._clipboard_notice = ft.Container(
            content=ft.Text(
                "요약 결과를 클립보드에 복사합니다. 브라우저에서 AI에 직접 붙여넣기 하여 사용하세요.",
                size=Typography.SMALL,
                color="#B45309",  # amber-700
            ),
            visible=False,
            bgcolor="#FFFBEB",  # amber-50
            border=ft.border.all(1, "#FDE68A"),  # amber-200
            border_radius=Radius.MD,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
        )

        self._expanded = True
        self._chevron = ft.Icon(ft.Icons.EXPAND_LESS, size=16, color=Colors.TEXT_SECONDARY)
        self._summary = ft.Text(
            self._get_summary_text(),
            size=Typography.SMALL,
            color=Colors.TEXT_MUTED,
            visible=False,
        )

        _header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.SMART_TOY, size=13, color=Colors.TEXT_MUTED),
                    ft.Text(
                        "AI 설정",
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

        self._expanded_content = ft.Column(
            controls=[
                self._model_selector.control,
                self._api_field.container,
                self._clipboard_notice,
            ],
            spacing=Spacing.SM,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            visible=True,
        )

        self.control = ft.Column(
            controls=[_header, self._summary, self._expanded_content],
            spacing=Spacing.XS,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _get_summary_text(self) -> str:
        engine = self._model_selector.get_engine()
        model = self._model_selector.get_model()
        api_key = self._api_field.get_value()
        engine_label = {
            "gemini": "Gemini", "openai": "OpenAI", "claude": "Claude",
            "grok": "Grok", "clipboard": "클립보드",
        }.get(engine, engine)
        key_status = "키 없음" if engine != "clipboard" and not api_key.strip() else ("API 불필요" if engine == "clipboard" else "키 있음")
        short_model = model.split("-")[0] if "-" in model else model
        return f"{engine_label} · {short_model} · {key_status}"

    def _toggle(self, e):
        self._expanded = not self._expanded
        self._expanded_content.visible = self._expanded
        self._summary.visible = not self._expanded
        self._chevron.icon = ft.Icons.EXPAND_LESS if self._expanded else ft.Icons.EXPAND_MORE
        self._expanded_content.update()
        self._summary.update()
        self._chevron.update()

    def _handle_engine_change(self, engine: str):
        """엔진 변경 시 API 키 라벨/활성 상태 업데이트"""
        new_label = _ENGINE_LABELS.get(engine, "AI API 키")
        self._api_field.control.label = new_label
        is_clipboard = engine == "clipboard"
        self._api_field.set_enabled(not is_clipboard)
        self._clipboard_notice.visible = is_clipboard

        # 엔진별 저장된 API 키 복원 (없으면 필드 비움)
        if not is_clipboard:
            saved_key = get_api_key_for_engine(engine)
            self._api_field.set_value(saved_key)

        if self._api_field.control.page:
            self._api_field.control.update()
        if self._clipboard_notice.page:
            self._clipboard_notice.update()

        if self._external_engine_cb:
            self._external_engine_cb(engine)

        # summary 업데이트
        self._summary.value = self._get_summary_text()
        try:
            if self._summary.page:
                self._summary.update()
        except Exception:
            pass

    def get_engine(self) -> str:
        return self._model_selector.get_engine()

    def get_model(self) -> str:
        return self._model_selector.get_model()

    def get_api_key(self) -> str:
        return self._api_field.get_value()

    def set_engine(self, engine: str):
        self._model_selector.set_engine(engine)

    def set_model(self, model_name: str):
        self._model_selector.set_model(model_name)

    def set_api_key(self, key: str):
        self._api_field.set_value(key)

    def set_enabled(self, enabled: bool):
        self._model_selector.set_enabled(enabled)
        if self.get_engine() != "clipboard":
            self._api_field.set_enabled(enabled)

    def clear(self):
        self._api_field.clear()
