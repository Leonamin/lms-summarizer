"""
강의 목록 다이얼로그 - 과목 선택 → 강의 선택 2단계 UI (Flet)
"""

from typing import List, Optional

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius, divider
from src.gui.config.course_models import (
    Course, CourseDetail, LectureItem, LectureType, VIDEO_LECTURE_TYPES,
)
from src.gui.core.file_manager import save_course_cache, load_course_cache
from src.gui.workers.course_list_worker import CourseListWorker


# LectureType → Material Icons 매핑
_TYPE_ICON_MAP = {
    LectureType.MOVIE: ft.Icons.MOVIE,
    LectureType.READYSTREAM: ft.Icons.MOVIE,
    LectureType.SCREENLECTURE: ft.Icons.MOVIE,
    LectureType.EVERLEC: ft.Icons.MOVIE,
    LectureType.MP4: ft.Icons.MOVIE,
    LectureType.ZOOM: ft.Icons.VIDEOCAM,
    LectureType.ASSIGNMENT: ft.Icons.ASSIGNMENT,
    LectureType.WIKI_PAGE: ft.Icons.DESCRIPTION,
    LectureType.QUIZ: ft.Icons.QUIZ,
    LectureType.DISCUSSION: ft.Icons.FORUM,
    LectureType.FILE: ft.Icons.FOLDER,
    LectureType.OTHER: ft.Icons.LIST,
}


class CourseListView:
    """과목 선택 → 강의 선택 2단계 다이얼로그"""

    def __init__(self, page: ft.Page, username: str, password: str, on_urls_selected=None):
        self._page = page
        self._username = username
        self._password = password
        self._on_urls_selected = on_urls_selected

        self._courses: List[Course] = []
        self._course_detail: Optional[CourseDetail] = None
        self._selected_lectures: dict[str, LectureItem] = {}  # url -> LectureItem
        self._worker: Optional[CourseListWorker] = None
        self._video_only = True

        # Phase 1: 과목 목록
        self._course_list = ft.ListView(spacing=2, expand=True)
        self._course_loading = ft.ProgressBar(
            color=Colors.PRIMARY,
            bgcolor=Colors.PRIMARY_BG,
            bar_height=3,
            visible=False,
        )
        self._course_status = ft.Text("", size=Typography.CAPTION, color=Colors.TEXT_MUTED)

        # Phase 2: 강의 목록
        self._lecture_list = ft.ListView(spacing=0, expand=True)
        self._lecture_loading = ft.ProgressBar(
            color=Colors.PRIMARY,
            bgcolor=Colors.PRIMARY_BG,
            bar_height=3,
            visible=False,
        )
        self._lecture_status = ft.Text("", size=Typography.CAPTION, color=Colors.TEXT_MUTED)
        self._confirm_btn = ft.ElevatedButton(
            text="선택한 강의 추가",
            icon=ft.Icons.CHECK,
            disabled=True,
            on_click=self._confirm_selection,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=Colors.PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
            ),
        )

        self._video_only_checkbox = ft.Checkbox(
            label="동영상 강의만 표시",
            value=True,
            active_color=Colors.PRIMARY,
            on_change=self._on_video_filter_changed,
        )

        # Phase 페이지들
        self._course_page = self._build_course_page()
        self._lecture_page = self._build_lecture_page()
        self._lecture_page.visible = False

        # 다이얼로그
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.SCHOOL, size=20, color=Colors.PRIMARY),
                    ft.Text("강의 목록", size=Typography.HEADING, weight=Typography.SEMI_BOLD),
                ],
                spacing=Spacing.SM,
            ),
            content=ft.Container(
                width=560,
                height=460,
                content=ft.Stack(
                    controls=[self._course_page, self._lecture_page],
                    expand=True,
                ),
            ),
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # 초기 로드
        self._try_load_cached_courses()

    def show(self):
        self._page.open(self.dialog)

    def close(self):
        self._cleanup_worker()
        self.dialog.open = False
        self._page.update()

    # ── Phase 1: 과목 목록 ──────────────────────────────────

    def _build_course_page(self) -> ft.Column:
        return ft.Column(
            controls=[
                ft.Text(
                    "과목을 클릭하여 주차별 강의 목록을 확인하세요.",
                    size=Typography.CAPTION,
                    color=Colors.TEXT_MUTED,
                ),
                self._course_loading,
                ft.Container(
                    content=self._course_list,
                    border_radius=Radius.SM,
                    border=ft.border.all(1, Colors.BORDER),
                    bgcolor=Colors.CARD,
                    expand=True,
                    padding=Spacing.XS,
                ),
                ft.Row(
                    controls=[
                        self._course_status,
                        ft.Container(expand=True),
                        ft.TextButton(
                            "새로고침",
                            icon=ft.Icons.REFRESH,
                            style=ft.ButtonStyle(color=Colors.PRIMARY),
                            on_click=lambda e: self._start_loading_courses(),
                        ),
                        ft.OutlinedButton(
                            "닫기",
                            icon=ft.Icons.CLOSE,
                            on_click=lambda e: self.close(),
                            style=ft.ButtonStyle(
                                color=Colors.TEXT_SECONDARY,
                                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=Spacing.SM,
            expand=True,
        )

    def _try_load_cached_courses(self):
        cached = load_course_cache()
        if cached:
            self._courses = [Course.from_dict(c) for c in cached]
            self._populate_course_list()
        else:
            self._start_loading_courses()

    def _start_loading_courses(self):
        self._cleanup_worker()
        self._course_list.controls.clear()
        self._course_status.value = "과목 목록을 불러오는 중..."
        self._course_loading.visible = True
        self._page.update()

        self._worker = CourseListWorker(
            self._username, self._password,
            on_courses_loaded=self._on_courses_loaded,
            on_error=self._on_load_error,
            on_finished=self._on_worker_finished,
        )
        self._worker.start()

    def _on_courses_loaded(self, courses):
        self._courses = courses
        self._course_loading.visible = False
        save_course_cache([c.to_dict() for c in courses])
        self._populate_course_list()
        self._page.update()

    def _populate_course_list(self):
        self._course_list.controls.clear()
        for course in self._courses:
            icon = ft.Icons.STAR if course.is_favorited else ft.Icons.STAR_BORDER
            icon_color = Colors.WARNING if course.is_favorited else Colors.TEXT_MUTED

            term_text = f"  ({course.term})" if course.term else ""
            tile = ft.ListTile(
                leading=ft.Icon(icon, size=18, color=icon_color),
                title=ft.Text(
                    course.long_name,
                    size=Typography.BODY,
                    color=Colors.TEXT,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                subtitle=ft.Text(term_text, size=Typography.SMALL, color=Colors.TEXT_MUTED) if course.term else None,
                on_click=lambda e, c=course: self._on_course_clicked(c),
                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                dense=True,
            )
            self._course_list.controls.append(tile)

        self._course_status.value = f"{len(self._courses)}개 과목"
        self._page.update()

    def _on_course_clicked(self, course: Course):
        self._start_loading_lectures(course)

    # ── Phase 2: 강의 목록 ──────────────────────────────────

    def _build_lecture_page(self) -> ft.Column:
        return ft.Column(
            controls=[
                ft.TextButton(
                    "< 과목 목록으로",
                    icon=ft.Icons.ARROW_BACK,
                    style=ft.ButtonStyle(color=Colors.PRIMARY),
                    on_click=lambda e: self._go_back_to_courses(),
                ),
                ft.Row(
                    controls=[
                        self._video_only_checkbox,
                        ft.Container(expand=True),
                        ft.TextButton(
                            "전체 선택",
                            icon=ft.Icons.SELECT_ALL,
                            style=ft.ButtonStyle(color=Colors.PRIMARY),
                            on_click=lambda e: self._select_all(),
                        ),
                        ft.TextButton(
                            "전체 해제",
                            icon=ft.Icons.DESELECT,
                            style=ft.ButtonStyle(color=Colors.TEXT_SECONDARY),
                            on_click=lambda e: self._deselect_all(),
                        ),
                    ],
                ),
                self._lecture_loading,
                ft.Container(
                    content=self._lecture_list,
                    border_radius=Radius.SM,
                    border=ft.border.all(1, Colors.BORDER),
                    bgcolor=Colors.CARD,
                    expand=True,
                    padding=Spacing.XS,
                ),
                ft.Row(
                    controls=[
                        self._lecture_status,
                        ft.Container(expand=True),
                        ft.OutlinedButton(
                            "취소",
                            icon=ft.Icons.CLOSE,
                            on_click=lambda e: self.close(),
                            style=ft.ButtonStyle(
                                color=Colors.TEXT_SECONDARY,
                                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                            ),
                        ),
                        self._confirm_btn,
                    ],
                ),
            ],
            spacing=Spacing.SM,
            expand=True,
        )

    def _start_loading_lectures(self, course: Course):
        self._cleanup_worker()
        # Phase 전환
        self._course_page.visible = False
        self._lecture_page.visible = True
        self._lecture_list.controls.clear()
        self._lecture_status.value = "강의 목록을 불러오는 중..."
        self._lecture_loading.visible = True
        self._selected_lectures.clear()
        self._confirm_btn.disabled = True
        self._page.update()

        self._worker = CourseListWorker(
            self._username, self._password,
            course=course,
            on_lectures_loaded=self._on_lectures_loaded,
            on_error=self._on_load_error,
            on_finished=self._on_worker_finished,
        )
        self._worker.start()

    def _on_lectures_loaded(self, detail: CourseDetail):
        self._course_detail = detail
        self._lecture_loading.visible = False
        self._populate_lecture_tree(detail)
        self._page.update()

    def _populate_lecture_tree(self, detail: CourseDetail):
        self._lecture_list.controls.clear()
        self._selected_lectures.clear()

        video_only = self._video_only

        for week in detail.weeks:
            lectures = week.video_lectures if video_only else week.lectures
            if not lectures:
                continue

            # 주차 헤더
            self._lecture_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        week.title,
                        size=Typography.BODY,
                        weight=Typography.SEMI_BOLD,
                        color=Colors.TEXT,
                    ),
                    padding=ft.padding.only(left=8, top=12, bottom=4),
                )
            )

            # 강의 아이템
            for lecture in lectures:
                parts = []
                if lecture.lesson_label:
                    parts.append(lecture.lesson_label)
                parts.append(lecture.title)
                if lecture.duration:
                    parts.append(f"({lecture.duration})")

                att_map = {"attendance": "출석", "late": "지각", "absent": "결석"}
                att_text = att_map.get(lecture.attendance, "")
                if att_text:
                    parts.append(f"[{att_text}]")

                if lecture.is_upcoming:
                    parts.append("[예정]")

                label_text = "  ".join(parts)
                icon = _TYPE_ICON_MAP.get(lecture.lecture_type, ft.Icons.LIST)
                is_selectable = lecture.is_video and lecture.item_url and not lecture.is_upcoming

                if is_selectable:
                    cb = ft.Checkbox(
                        value=False,
                        active_color=Colors.PRIMARY,
                        on_change=lambda e, lec=lecture: self._on_lecture_checked(lec, e.control.value),
                    )
                    tile = ft.ListTile(
                        leading=ft.Icon(icon, size=16, color=Colors.PRIMARY),
                        title=ft.Text(label_text, size=Typography.CAPTION, color=Colors.TEXT),
                        trailing=cb,
                        dense=True,
                        on_click=lambda e, checkbox=cb, lec=lecture: self._toggle_checkbox(checkbox, lec),
                    )
                else:
                    color = Colors.TEXT_MUTED if lecture.is_upcoming else Colors.TEXT_SECONDARY
                    tile = ft.ListTile(
                        leading=ft.Icon(icon, size=16, color=Colors.TEXT_MUTED),
                        title=ft.Text(label_text, size=Typography.CAPTION, color=color),
                        dense=True,
                    )

                self._lecture_list.controls.append(tile)

        self._update_selection_count()

    def _toggle_checkbox(self, checkbox: ft.Checkbox, lecture: LectureItem):
        checkbox.value = not checkbox.value
        self._on_lecture_checked(lecture, checkbox.value)
        self._page.update()

    def _on_lecture_checked(self, lecture: LectureItem, checked: bool):
        if checked and lecture.item_url:
            self._selected_lectures[lecture.item_url] = lecture
        elif lecture.item_url in self._selected_lectures:
            del self._selected_lectures[lecture.item_url]
        self._update_selection_count()
        self._page.update()

    def _update_selection_count(self):
        total_videos = 0
        if self._course_detail:
            total_videos = len(self._course_detail.all_video_lectures)
        count = len(self._selected_lectures)
        self._lecture_status.value = f"{total_videos}개 동영상 중 {count}개 선택"
        self._confirm_btn.disabled = count == 0
        self._confirm_btn.text = f"선택한 강의 추가 ({count})"

    def _select_all(self):
        for control in self._lecture_list.controls:
            if isinstance(control, ft.ListTile) and control.trailing and isinstance(control.trailing, ft.Checkbox):
                control.trailing.value = True
        # 전체 선택 가능한 강의 추가
        if self._course_detail:
            for week in self._course_detail.weeks:
                lectures = week.video_lectures if self._video_only else week.lectures
                for lec in lectures:
                    if lec.is_video and lec.item_url and not lec.is_upcoming:
                        self._selected_lectures[lec.item_url] = lec
        self._update_selection_count()
        self._page.update()

    def _deselect_all(self):
        for control in self._lecture_list.controls:
            if isinstance(control, ft.ListTile) and control.trailing and isinstance(control.trailing, ft.Checkbox):
                control.trailing.value = False
        self._selected_lectures.clear()
        self._update_selection_count()
        self._page.update()

    def _on_video_filter_changed(self, e):
        self._video_only = e.control.value
        if self._course_detail:
            self._populate_lecture_tree(self._course_detail)
            self._page.update()

    # ── 네비게이션 ───────────────────────────────────────────

    def _go_back_to_courses(self):
        self._cleanup_worker()
        self._course_page.visible = True
        self._lecture_page.visible = False
        self._page.update()

    def _confirm_selection(self, e=None):
        urls = [lec.full_url for lec in self._selected_lectures.values()]
        self.close()
        if self._on_urls_selected and urls:
            self._on_urls_selected(urls)

    # ── 에러 / 정리 ──────────────────────────────────────────

    def _on_load_error(self, error_msg: str):
        self._course_loading.visible = False
        self._lecture_loading.visible = False
        if self._course_page.visible:
            self._course_status.value = f"오류: {error_msg}"
        else:
            self._lecture_status.value = f"오류: {error_msg}"
        self._page.update()

    def _on_worker_finished(self):
        self._course_loading.visible = False
        self._lecture_loading.visible = False
        try:
            self._page.update()
        except Exception:
            pass

    def _cleanup_worker(self):
        if self._worker and self._worker.is_running():
            self._worker.request_cancel()
            self._worker.join(timeout=3)
        self._worker = None
