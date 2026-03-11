"""
계정 입력 섹션 - 학번, 비밀번호
"""

from typing import Dict

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.gui.config.settings import INPUT_FIELD_CONFIGS
from src.gui.components.input_field import InputField


class AccountSection:
    """학번/비밀번호 입력 섹션"""

    def __init__(self):
        self._fields: Dict[str, InputField] = {}

        # student_id, password 필드 생성
        for name in ('student_id', 'password'):
            config = INPUT_FIELD_CONFIGS[name]
            self._fields[name] = InputField(config)

        self.control = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=13, color=Colors.TEXT_MUTED),
                        ft.Text(
                            "계정",
                            size=Typography.SMALL,
                            weight=Typography.SEMI_BOLD,
                            color=Colors.TEXT_MUTED,
                        ),
                    ],
                    spacing=Spacing.XS,
                ),
                self._fields['student_id'].container,
                self._fields['password'].container,
            ],
            spacing=Spacing.SM,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def get_values(self) -> Dict[str, str]:
        """학번/비밀번호 값 반환"""
        return {name: field.get_value() for name, field in self._fields.items()}

    def set_values(self, values: Dict[str, str]):
        """값 설정"""
        for name, value in values.items():
            if name in self._fields and value:
                self._fields[name].set_value(value)

    def set_enabled(self, enabled: bool):
        """활성/비활성"""
        for field in self._fields.values():
            field.set_enabled(enabled)

    def set_error(self, field_name: str, error_text: str):
        """특정 필드에 에러 표시"""
        if field_name in self._fields:
            self._fields[field_name].set_error(error_text)

    def clear_error(self):
        """모든 에러 초기화"""
        for field in self._fields.values():
            field.clear_error()

    def clear(self):
        """모든 필드 초기화"""
        for field in self._fields.values():
            field.clear()
