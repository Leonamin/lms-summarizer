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

        # 클립보드 모드 안내 텍스트
        self._clipboard_notice = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=Colors.INFO),
                    ft.Text(
                        "클립보드에 복사 후 ChatGPT를 엽니다.",
                        size=Typography.SMALL,
                        color=Colors.INFO,
                    ),
                ],
                spacing=Spacing.XS,
            ),
            visible=False,
            padding=ft.padding.only(left=4),
        )

        self.control = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.AUTO_AWESOME, size=14, color=Colors.TEXT_MUTED),
                        ft.Text(
                            "AI 설정",
                            size=Typography.CAPTION,
                            weight=Typography.SEMI_BOLD,
                            color=Colors.TEXT_SECONDARY,
                        ),
                    ],
                    spacing=Spacing.XS,
                ),
                self._model_selector.control,
                self._api_field.container,
                self._clipboard_notice,
            ],
            spacing=Spacing.XS,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _handle_engine_change(self, engine: str):
        """엔진 변경 시 API 키 라벨/활성 상태 업데이트"""
        new_label = _ENGINE_LABELS.get(engine, "AI API 키")
        self._api_field.control.label = new_label
        is_clipboard = engine == "clipboard"
        self._api_field.set_enabled(not is_clipboard)
        self._clipboard_notice.visible = is_clipboard

        # 엔진별 저장된 API 키 복원
        if not is_clipboard:
            saved_key = get_api_key_for_engine(engine)
            if saved_key:
                self._api_field.set_value(saved_key)

        if self._api_field.control.page:
            self._api_field.control.update()
        if self._clipboard_notice.page:
            self._clipboard_notice.update()

        if self._external_engine_cb:
            self._external_engine_cb(engine)

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
