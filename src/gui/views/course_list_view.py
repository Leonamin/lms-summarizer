"""
강의 목록 다이얼로그 - 과목 선택 → 강의 선택 2단계 UI (Flet)
- Step 1: 과목 목록 (별 아이콘, 학기 배지, 화살표)
- Step 2: 주차별 강의 목록 (재생 아이콘, 시간, 출석 배지, 체크박스)
"""

from typing import List, Optional

import flet as ft

from src.gui.theme import Colors, Typography, Spacing, Radius, divider
from src.gui.config.course_models import (
    Course, CourseDetail, LectureItem, LectureType, VIDEO_LECTURE_TYPES,
)
from src.gui.core.file_manager import save_course_cache, load_course_cache
from src.gui.workers.course_list_worker import CourseListWorker


# 출석 상태 매핑
_ATTENDANCE_MAP = {"attendance": "출석", "late": "지각", "absent": "결석"}
_ATTENDANCE_COLOR = {"attendance": Colors.SUCCESS, "late": Colors.WARNING, "absent": Colors.ERROR}


class CourseListView:
    """과목 선택 -> 강의 선택 2단계 다이얼로그"""

    def __init__(self, page: ft.Page, username: str, password: str, on_urls_selected=None):
        self._page = page
        self._username = username
        self._password = password
        self._on_urls_selected = on_urls_selected

        self._courses: List[Course] = []
        self._course_detail: Optional[CourseDetail] = None
        self._selected_course: Optional[Course] = None
        self._selected_lectures: dict[str, LectureItem] = {}
        self._worker: Optional[CourseListWorker] = None
        self._video_only = True

        # ── 공통 UI ──────────────────────────────────────
        self._step_text = ft.Text(
            "1 / 2",
            size=Typography.CAPTION,
            color=Colors.TEXT_MUTED,
        )
        self._step_bar = ft.ProgressBar(
            value=0.5,
            color=Colors.PRIMARY,
            bgcolor=Colors.PRIMARY_BG,
            bar_height=3,
        )

        # ── Step 1: 과목 목록 ────────────────────────────
        self._course_list = ft.ListView(spacing=2, expand=True)
        self._course_loading = ft.ProgressBar(
            color=Colors.PRIMARY,
            bgcolor=Colors.PRIMARY_BG,
            bar_height=3,
            visible=False,
        )
        self._course_status = ft.Text("", size=Typography.CAPTION, color=Colors.TEXT_MUTED)

        # ── Step 2: 강의 목록 ────────────────────────────
        self._lecture_list = ft.ListView(spacing=0, expand=True)
        self._lecture_loading = ft.ProgressBar(
            color=Colors.PRIMARY,
            bgcolor=Colors.PRIMARY_BG,
            bar_height=3,
            visible=False,
        )
        self._lecture_status = ft.Text("", size=Typography.CAPTION, color=Colors.TEXT_MUTED)

        self._confirm_btn = ft.ElevatedButton(
            content=ft.Text("선택한 강의 추가"),
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

        # ── 타이틀 ──────────────────────────────────────
        self._title_icon = ft.Icon(ft.Icons.SCHOOL, size=20, color=Colors.PRIMARY)
        self._title_text = ft.Text(
            "강의 목록",
            size=Typography.HEADING,
            weight=Typography.SEMI_BOLD,
            expand=True,
        )
        self._subtitle_text = ft.Text(
            "과목을 클릭하여 주차별 강의를 확인하세요.",
            size=Typography.CAPTION,
            color=Colors.TEXT_MUTED,
        )

        # ── Phase 페이지 조립 ────────────────────────────
        self._course_page = self._build_course_page()
        self._lecture_page = self._build_lecture_page()
        self._lecture_page.visible = False

        # ── 다이얼로그 ──────────────────────────────────
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self._title_icon,
                            self._title_text,
                            self._step_text,
                        ],
                        spacing=Spacing.SM,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self._subtitle_text,
                    self._step_bar,
                ],
                spacing=Spacing.XS,
            ),
            content=ft.Container(
                width=520,
                height=480,
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
        self._page.show_dialog(self.dialog)

    def close(self):
        self._cleanup_worker()
        self.dialog.open = False
        self._page.update()

    # ── Step 1: 과목 목록 ────────────────────────────────

    def _build_course_page(self) -> ft.Column:
        return ft.Column(
            controls=[
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
                            content=ft.Text("새로고침"),
                            icon=ft.Icons.REFRESH,
                            style=ft.ButtonStyle(color=Colors.PRIMARY),
                            on_click=lambda e: self._start_loading_courses(),
                        ),
                        ft.OutlinedButton(
                            content=ft.Text("닫기"),
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
        try:
            save_course_cache([c.to_dict() for c in courses])
        except Exception as e:
            print(f"[WARNING] 과목 캐시 저장 실패 (무시): {e}")
        self._populate_course_list()
        self._page.update()

    def _populate_course_list(self):
        self._course_list.controls.clear()
        for course in self._courses:
            # 별 아이콘 (즐겨찾기: accent orange 배경)
            if course.is_favorited:
                star = ft.Container(
                    content=ft.Icon(ft.Icons.STAR, size=14, color=ft.Colors.WHITE),
                    width=28, height=28,
                    border_radius=14,
                    bgcolor=Colors.ACCENT,
                    alignment=ft.Alignment(0, 0),
                )
            else:
                star = ft.Container(
                    content=ft.Icon(ft.Icons.STAR_BORDER, size=14, color=Colors.TEXT_MUTED),
                    width=28, height=28,
                    border_radius=14,
                    bgcolor=Colors.SURFACE,
                    alignment=ft.Alignment(0, 0),
                )

            # 학기 배지
            term_badge = None
            if course.term:
                term_badge = ft.Text(
                    course.term,
                    size=Typography.SMALL,
                    color=Colors.TEXT_MUTED,
                )

            # 과목 행
            row_controls = [
                star,
                ft.Column(
                    controls=[
                        ft.Text(
                            course.long_name,
                            size=Typography.BODY,
                            weight=Typography.SEMI_BOLD,
                            color=Colors.TEXT,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        *([ term_badge ] if term_badge else []),
                    ],
                    spacing=0,
                    expand=True,
                ),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=Colors.TEXT_MUTED),
            ]

            tile = ft.Container(
                content=ft.Row(
                    controls=row_controls,
                    spacing=Spacing.SM,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.symmetric(horizontal=Spacing.SM, vertical=Spacing.SM),
                border_radius=Radius.SM,
                ink=True,
                on_click=lambda e, c=course: self._on_course_clicked(c),
            )
            self._course_list.controls.append(tile)

        self._course_status.value = f"{len(self._courses)}개 과목"
        self._page.update()

    def _on_course_clicked(self, course: Course):
        self._selected_course = course
        self._start_loading_lectures(course)

    # ── Step 2: 강의 목록 ────────────────────────────────

    def _build_lecture_page(self) -> ft.Column:
        return ft.Column(
            controls=[
                # 툴바: 필터 + 선택 버튼
                ft.Row(
                    controls=[
                        self._video_only_checkbox,
                        ft.Container(expand=True),
                        ft.TextButton(
                            content=ft.Text("모두 선택"),
                            icon=ft.Icons.SELECT_ALL,
                            style=ft.ButtonStyle(
                                color=Colors.PRIMARY,
                                text_style=ft.TextStyle(size=Typography.SMALL),
                            ),
                            on_click=lambda e: self._select_all(),
                        ),
                        ft.Text("|", size=Typography.CAPTION, color=Colors.BORDER),
                        ft.TextButton(
                            content=ft.Text("해제"),
                            icon=ft.Icons.DESELECT,
                            style=ft.ButtonStyle(
                                color=Colors.TEXT_MUTED,
                                text_style=ft.TextStyle(size=Typography.SMALL),
                            ),
                            on_click=lambda e: self._deselect_all(),
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
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
                            content=ft.Text("취소"),
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

        # Step 전환: 1 -> 2
        self._course_page.visible = False
        self._lecture_page.visible = True
        self._step_text.value = "2 / 2"
        self._step_bar.value = 1.0
        self._title_icon.name = ft.Icons.ARROW_BACK
        self._title_icon.color = Colors.PRIMARY
        self._title_text.value = course.long_name
        self._subtitle_text.value = ""
        # 타이틀 아이콘을 뒤로가기 버튼으로 변환
        self._title_icon.on_click = lambda e: self._go_back_to_courses()

        self._lecture_list.controls.clear()
        self._lecture_status.value = "강의 목록을 불러오는 중..."
        self._lecture_loading.visible = True
        self._selected_lectures.clear()
        self._confirm_btn.disabled = True
        self._confirm_btn.content.value = "선택한 강의 추가"
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

            # 주차 헤더 (회색 배경)
            self._lecture_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        week.title,
                        size=Typography.CAPTION,
                        weight=Typography.SEMI_BOLD,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    bgcolor=Colors.SURFACE,
                    border_radius=Radius.SM,
                    padding=ft.padding.symmetric(horizontal=Spacing.SM, vertical=Spacing.XS),
                    margin=ft.margin.only(top=Spacing.SM if week.week_number > 1 else 0),
                )
            )

            # 강의 아이템
            for lecture in lectures:
                self._lecture_list.controls.append(
                    self._build_lecture_row(lecture)
                )

        self._update_selection_count()

    def _build_lecture_row(self, lecture: LectureItem) -> ft.Container:
        """개별 강의 행 생성"""
        is_selectable = lecture.is_video and lecture.item_url and not lecture.is_upcoming
        is_video = lecture.is_video

        # 아이콘
        icon_name = ft.Icons.PLAY_ARROW if is_video else ft.Icons.DESCRIPTION
        icon_color = Colors.PRIMARY if is_selectable else Colors.TEXT_MUTED

        # 제목
        title_color = Colors.TEXT if is_selectable else (Colors.TEXT_MUTED if lecture.is_upcoming else Colors.TEXT_SECONDARY)

        # 부가 정보 (시간, 출석)
        info_controls = []
        if lecture.duration:
            info_controls.append(
                ft.Text(
                    lecture.duration,
                    size=Typography.SMALL,
                    color=Colors.TEXT_MUTED,
                )
            )

        att_text = _ATTENDANCE_MAP.get(lecture.attendance)
        if att_text:
            att_color = _ATTENDANCE_COLOR.get(lecture.attendance, Colors.TEXT_MUTED)
            info_controls.append(
                ft.Container(
                    content=ft.Text(att_text, size=9, color=att_color, weight=Typography.MEDIUM),
                    border=ft.border.all(1, att_color),
                    border_radius=Radius.SM,
                    padding=ft.padding.symmetric(horizontal=4, vertical=1),
                )
            )

        if lecture.is_upcoming:
            info_controls.append(
                ft.Container(
                    content=ft.Text("예정", size=9, color=Colors.TEXT_MUTED),
                    border=ft.border.all(1, Colors.BORDER),
                    border_radius=Radius.SM,
                    padding=ft.padding.symmetric(horizontal=4, vertical=1),
                )
            )

        # 체크박스 (선택 가능한 경우만)
        cb = None
        if is_selectable:
            cb = ft.Checkbox(
                value=False,
                active_color=Colors.PRIMARY,
                on_change=lambda e, lec=lecture: self._on_lecture_checked(lec, e.control.value),
            )

        # 텍스트 영역
        title_text = lecture.title
        if lecture.lesson_label:
            title_text = f"{lecture.lesson_label}  {title_text}"

        row_controls = [
            ft.Icon(icon_name, size=16, color=icon_color),
            ft.Column(
                controls=[
                    ft.Text(
                        title_text,
                        size=Typography.CAPTION,
                        color=title_color,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    *(
                        [ft.Row(controls=info_controls, spacing=Spacing.XS)]
                        if info_controls else []
                    ),
                ],
                spacing=0,
                expand=True,
            ),
        ]
        if cb:
            row_controls.append(cb)

        container = ft.Container(
            content=ft.Row(
                controls=row_controls,
                spacing=Spacing.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=Spacing.SM, vertical=Spacing.XS),
            border_radius=Radius.SM,
            ink=is_selectable,
            on_click=(lambda e, checkbox=cb, lec=lecture: self._toggle_checkbox(checkbox, lec)) if is_selectable else None,
        )
        return container

    def _toggle_checkbox(self, checkbox: ft.Checkbox, lecture: LectureItem):
        if checkbox:
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
        self._lecture_status.value = f"{total_videos}개 중 {count}개 선택"
        self._confirm_btn.disabled = count == 0
        self._confirm_btn.content.value = f"선택한 강의 추가 ({count})" if count > 0 else "선택한 강의 추가"

    def _select_all(self):
        for control in self._lecture_list.controls:
            if isinstance(control, ft.Container) and control.content and isinstance(control.content, ft.Row):
                row = control.content
                # 마지막 요소가 Checkbox인 경우
                if row.controls and isinstance(row.controls[-1], ft.Checkbox):
                    row.controls[-1].value = True
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
            if isinstance(control, ft.Container) and control.content and isinstance(control.content, ft.Row):
                row = control.content
                if row.controls and isinstance(row.controls[-1], ft.Checkbox):
                    row.controls[-1].value = False
        self._selected_lectures.clear()
        self._update_selection_count()
        self._page.update()

    def _on_video_filter_changed(self, e):
        self._video_only = e.control.value
        if self._course_detail:
            self._populate_lecture_tree(self._course_detail)
            self._page.update()

    # ── 네비게이션 ───────────────────────────────────────

    def _go_back_to_courses(self):
        self._cleanup_worker()
        self._course_page.visible = True
        self._lecture_page.visible = False

        # Step 전환: 2 -> 1
        self._step_text.value = "1 / 2"
        self._step_bar.value = 0.5
        self._title_icon.name = ft.Icons.SCHOOL
        self._title_icon.color = Colors.PRIMARY
        self._title_icon.on_click = None
        self._title_text.value = "강의 목록"
        self._subtitle_text.value = "과목을 클릭하여 주차별 강의를 확인하세요."

        self._page.update()

    def _confirm_selection(self, e=None):
        urls = [lec.full_url for lec in self._selected_lectures.values()]
        self.close()
        if self._on_urls_selected and urls:
            self._on_urls_selected(urls)

    # ── 에러 / 정리 ──────────────────────────────────────

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
