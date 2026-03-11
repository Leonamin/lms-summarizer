"""
강의 입력 섹션 - 탭 기반 (목록 선택 / URL 직접 입력)
"""

from typing import List

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.gui.config.settings import INPUT_FIELD_CONFIGS
from src.gui.components.input_field import InputField


class LectureSection:
    """강의 입력: 탭으로 '목록에서 선택' / 'URL 직접 입력' 전환"""

    def __init__(self, on_open_course_list=None):
        self._on_open_course_list = on_open_course_list

        # URL 직접 입력 필드
        self._url_field = InputField(INPUT_FIELD_CONFIGS['urls'])

        # 선택된 강의 표시 (목록에서 선택 시)
        self._selected_count = ft.Text(
            "선택된 강의가 없습니다.",
            size=Typography.CAPTION,
            color=Colors.TEXT_MUTED,
            text_align=ft.TextAlign.CENTER,
        )

        # 목록 선택 탭 콘텐츠
        self._list_tab_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.MENU_BOOK, size=32, color=Colors.TEXT_MUTED),
                                self._selected_count,
                                ft.ElevatedButton(
                                    content=ft.Text("강의 목록에서 선택"),
                                    icon=ft.Icons.MENU_BOOK,
                                    on_click=self._handle_open_course_list,
                                    style=ft.ButtonStyle(
                                        color=ft.Colors.WHITE,
                                        bgcolor=Colors.PRIMARY,
                                        shape=ft.RoundedRectangleBorder(radius=Radius.LG),
                                        padding=ft.padding.symmetric(horizontal=20, vertical=10),
                                        text_style=ft.TextStyle(size=Typography.BODY),
                                    ),
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=Spacing.SM,
                        ),
                        alignment=ft.Alignment.CENTER,
                        expand=True,
                    ),
                ],
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            expand=True,
            padding=Spacing.MD,
        )

        # URL 직접 입력 탭 콘텐츠
        self._url_tab_content = ft.Container(
            content=self._url_field.container,
            expand=True,
            padding=Spacing.SM,
        )

        # 탭 (Flet 0.81: Tabs = TabBar + TabBarView)
        self._tab_bar = ft.TabBar(
            tabs=[
                ft.Tab(label="목록에서 선택", icon=ft.Icons.LIST),
                ft.Tab(label="URL 직접 입력", icon=ft.Icons.LINK),
            ],
            indicator_color=Colors.PRIMARY,
            label_color=Colors.PRIMARY,
            unselected_label_color=Colors.TEXT_MUTED,
        )

        self._tab_view = ft.TabBarView(
            controls=[self._list_tab_content, self._url_tab_content],
        )

        self._tabs = ft.Tabs(
            content=ft.Column(
                controls=[self._tab_bar, self._tab_view],
                spacing=0,
                expand=True,
            ),
            length=2,
            selected_index=0,
            on_change=self._handle_tab_change,
        )

        self.control = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.MOVIE, size=14, color=Colors.TEXT_MUTED),
                        ft.Text(
                            "강의 선택",
                            size=Typography.CAPTION,
                            weight=Typography.SEMI_BOLD,
                            color=Colors.TEXT_SECONDARY,
                        ),
                    ],
                    spacing=Spacing.XS,
                ),
                self._tabs,
            ],
            spacing=Spacing.XS,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _handle_tab_change(self, e):
        # TabBarView가 자동으로 콘텐츠 전환 처리
        pass

    def _handle_open_course_list(self, e):
        if self._on_open_course_list:
            self._on_open_course_list()

    def get_urls(self) -> str:
        """URL 텍스트 반환 (직접 입력 탭의 값)"""
        return self._url_field.get_value()

    def set_urls(self, urls_text: str):
        """URL 텍스트 설정"""
        self._url_field.set_value(urls_text)

    def update_selected_count(self, count: int):
        """목록에서 선택된 강의 수 업데이트"""
        if count > 0:
            self._selected_count.value = f"{count}개 강의가 선택되었습니다."
            self._selected_count.color = Colors.PRIMARY
        else:
            self._selected_count.value = "선택된 강의가 없습니다."
            self._selected_count.color = Colors.TEXT_MUTED

    def set_enabled(self, enabled: bool):
        self._url_field.set_enabled(enabled)

    def clear(self):
        self._url_field.clear()
        self.update_selected_count(0)
