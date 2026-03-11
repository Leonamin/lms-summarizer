"""
저장 경로 섹션 - 경로 표시 + 열기/변경 버튼
"""

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius
from src.gui.core.file_manager import (
    ensure_downloads_directory, set_downloads_directory, open_in_file_explorer,
)


class StoragePath:
    """저장 경로 표시 및 변경"""

    def __init__(self, on_path_changed=None):
        self._on_path_changed = on_path_changed
        self._folder_picker = ft.FilePicker()

        self._path_text = ft.Text(
            ensure_downloads_directory(),
            size=Typography.SMALL,
            color=Colors.TEXT_SECONDARY,
            expand=True,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        self.control = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.FOLDER, size=14, color=Colors.TEXT_MUTED),
                            ft.Text(
                                "저장 경로",
                                size=Typography.CAPTION,
                                weight=Typography.SEMI_BOLD,
                                color=Colors.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=Spacing.XS,
                    ),
                    ft.Container(
                        content=self._path_text,
                        bgcolor=Colors.SURFACE,
                        border_radius=Radius.SM,
                        border=ft.border.all(1, Colors.BORDER),
                        padding=ft.padding.symmetric(horizontal=8, vertical=6),
                    ),
                    ft.Row(
                        controls=[
                            ft.OutlinedButton(
                                content=ft.Text("열기"),
                                icon=ft.Icons.FOLDER_OPEN,
                                on_click=self._open_in_finder,
                                style=ft.ButtonStyle(
                                    color=Colors.PRIMARY,
                                    shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                                    text_style=ft.TextStyle(size=Typography.SMALL),
                                ),
                            ),
                            ft.OutlinedButton(
                                content=ft.Text("변경"),
                                on_click=self._change_path,
                                style=ft.ButtonStyle(
                                    color=Colors.PRIMARY,
                                    shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                                    text_style=ft.TextStyle(size=Typography.SMALL),
                                ),
                            ),
                        ],
                        spacing=Spacing.XS,
                    ),
                ],
                spacing=Spacing.SM,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )

    def _open_in_finder(self, e=None):
        open_in_file_explorer(ensure_downloads_directory())

    async def _change_path(self, e=None):
        path = await self._folder_picker.get_directory_path(
            dialog_title="저장 경로 선택",
            initial_directory=ensure_downloads_directory(),
        )
        if path:
            set_downloads_directory(path)
            self._path_text.value = path
            if self._on_path_changed:
                self._on_path_changed(path)
            if self._path_text.page:
                self._path_text.page.update()

    def get_path(self) -> str:
        return self._path_text.value or ensure_downloads_directory()
