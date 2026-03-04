"""
강의 목록 다이얼로그 - 과목 선택 → 강의 선택 2단계 UI
"""

from typing import List, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QCheckBox, QStackedWidget, QWidget, QFrame, QSizePolicy,
    QProgressBar,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor

from src.gui.config.constants import Colors
from src.gui.config.styles import StyleSheet
from src.gui.config.course_models import (
    Course, CourseDetail, LectureItem, Week, LectureType, VIDEO_LECTURE_TYPES,
)
from src.gui.ui.components.buttons import AppButton
from src.gui.ui.components.icons import AppIcons
from src.gui.core.file_manager import (
    save_course_cache, load_course_cache,
)
from src.gui.workers.course_list_worker import CourseListWorker


# LectureType → 아이콘 이름 매핑
_TYPE_ICON_MAP = {
    LectureType.MOVIE: "movie",
    LectureType.READYSTREAM: "movie",
    LectureType.SCREENLECTURE: "movie",
    LectureType.EVERLEC: "movie",
    LectureType.MP4: "movie",
    LectureType.ZOOM: "video",
    LectureType.ASSIGNMENT: "assignment",
    LectureType.WIKI_PAGE: "wiki",
    LectureType.QUIZ: "quiz",
    LectureType.DISCUSSION: "log",
    LectureType.FILE: "folder",
    LectureType.OTHER: "list",
}


class CourseListDialog(QDialog):
    """과목 선택 → 강의 선택 2단계 다이얼로그"""

    def __init__(self, parent=None, username: str = "", password: str = ""):
        super().__init__(parent)
        self._username = username
        self._password = password
        self._courses: List[Course] = []
        self._course_detail: Optional[CourseDetail] = None
        self._selected_urls: List[str] = []
        self._worker: Optional[CourseListWorker] = None

        self.setWindowTitle("강의 목록")
        self.setModal(True)
        self.setMinimumSize(560, 480)
        self.resize(600, 560)
        self.setStyleSheet(StyleSheet.modal_window())

        self._setup_ui()
        self._try_load_cached_courses()

    # ── UI 구성 ────────────────────────────────────────────────

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_course_page())
        self._stack.addWidget(self._build_lecture_page())

        main_layout.addWidget(self._stack)
        self.setLayout(main_layout)

    # ── Phase 1: 과목 선택 ──────────────────────────────────────

    def _build_course_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)

        # 제목
        title = AppIcons.label('graduation', '강의 목록', icon_size=18)
        title.setStyleSheet(StyleSheet.modal_title())
        layout.addWidget(title)
        layout.addWidget(self._make_divider())

        # 설명
        desc = QLabel("과목을 더블클릭하여 주차별 강의 목록을 확인하세요.")
        desc.setStyleSheet(f"color: {Colors.TEXT_LIGHT}; font-size: 12px;")
        layout.addWidget(desc)

        # 로딩 표시
        self._course_loading_bar = QProgressBar()
        self._course_loading_bar.setRange(0, 0)  # indeterminate
        self._course_loading_bar.setFixedHeight(4)
        self._course_loading_bar.setTextVisible(False)
        self._course_loading_bar.setStyleSheet(StyleSheet.progress_bar())
        self._course_loading_bar.setVisible(False)
        layout.addWidget(self._course_loading_bar)

        # 과목 리스트
        self._course_list = QListWidget()
        self._course_list.setStyleSheet(StyleSheet.course_list_widget())
        self._course_list.setIconSize(QSize(18, 18))
        self._course_list.itemDoubleClicked.connect(self._on_course_double_clicked)
        layout.addWidget(self._course_list, stretch=1)

        # 상태 바 + 버튼
        bottom_row = QHBoxLayout()

        self._course_status_label = QLabel()
        self._course_status_label.setStyleSheet(StyleSheet.status_label())
        bottom_row.addWidget(self._course_status_label)

        bottom_row.addStretch()

        refresh_btn = AppButton("새로고침", "text")
        refresh_btn.setIcon(AppIcons.icon('refresh'))
        refresh_btn.clicked.connect(self._start_loading_courses)
        bottom_row.addWidget(refresh_btn)

        close_btn = AppButton("닫기", "outline")
        close_btn.setIcon(AppIcons.icon('cancel'))
        close_btn.clicked.connect(self.reject)
        bottom_row.addWidget(close_btn)

        layout.addLayout(bottom_row)
        return page

    # ── Phase 2: 강의 선택 ──────────────────────────────────────

    def _build_lecture_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)

        # 제목 + 뒤로가기
        self._lecture_title = AppIcons.label('book', '강의 선택', icon_size=18)
        self._lecture_title.setStyleSheet(StyleSheet.modal_title())
        layout.addWidget(self._lecture_title)

        back_btn = AppButton("< 과목 목록으로", "text")
        back_btn.setIcon(AppIcons.icon('back'))
        back_btn.clicked.connect(self._go_back_to_courses)
        layout.addWidget(back_btn, alignment=Qt.AlignLeft)

        layout.addWidget(self._make_divider())

        # 필터 + 선택 버튼
        filter_row = QHBoxLayout()

        self._video_only_checkbox = QCheckBox("동영상 강의만 표시")
        self._video_only_checkbox.setStyleSheet(StyleSheet.checkbox())
        self._video_only_checkbox.setChecked(True)
        self._video_only_checkbox.stateChanged.connect(self._apply_video_filter)
        filter_row.addWidget(self._video_only_checkbox)

        filter_row.addStretch()

        select_all_btn = AppButton("전체 선택", "text")
        select_all_btn.setIcon(AppIcons.icon('select_all'))
        select_all_btn.clicked.connect(self._select_all)
        filter_row.addWidget(select_all_btn)

        deselect_all_btn = AppButton("전체 해제", "text")
        deselect_all_btn.setIcon(AppIcons.icon('deselect_all'))
        deselect_all_btn.clicked.connect(self._deselect_all)
        filter_row.addWidget(deselect_all_btn)

        layout.addLayout(filter_row)

        # 로딩 표시
        self._lecture_loading_bar = QProgressBar()
        self._lecture_loading_bar.setRange(0, 0)  # indeterminate
        self._lecture_loading_bar.setFixedHeight(4)
        self._lecture_loading_bar.setTextVisible(False)
        self._lecture_loading_bar.setStyleSheet(StyleSheet.progress_bar())
        self._lecture_loading_bar.setVisible(False)
        layout.addWidget(self._lecture_loading_bar)

        # 강의 트리
        self._lecture_tree = QTreeWidget()
        self._lecture_tree.setHeaderHidden(True)
        self._lecture_tree.setStyleSheet(StyleSheet.lecture_tree_widget())
        self._lecture_tree.setIconSize(QSize(16, 16))
        self._lecture_tree.itemChanged.connect(self._on_tree_item_changed)
        layout.addWidget(self._lecture_tree, stretch=1)

        # 상태 바 + 확인 버튼
        bottom_row = QHBoxLayout()

        self._lecture_status_label = QLabel()
        self._lecture_status_label.setStyleSheet(StyleSheet.status_label())
        bottom_row.addWidget(self._lecture_status_label)

        bottom_row.addStretch()

        cancel_btn = AppButton("취소", "outline")
        cancel_btn.setIcon(AppIcons.icon('cancel'))
        cancel_btn.clicked.connect(self.reject)
        bottom_row.addWidget(cancel_btn)

        self._confirm_btn = AppButton("선택한 강의 추가", "filled")
        self._confirm_btn.setIcon(AppIcons.icon('start', color='white'))
        self._confirm_btn.clicked.connect(self._confirm_selection)
        self._confirm_btn.setEnabled(False)
        bottom_row.addWidget(self._confirm_btn)

        layout.addLayout(bottom_row)
        return page

    # ── 과목 로딩 ──────────────────────────────────────────────

    def _try_load_cached_courses(self):
        """캐시에서 과목 목록 로드 시도. 없으면 서버에서 로드."""
        cached = load_course_cache()
        if cached:
            self._courses = [Course.from_dict(c) for c in cached]
            self._populate_course_list()
        else:
            self._start_loading_courses()

    def _start_loading_courses(self):
        """서버에서 과목 목록 로드"""
        self._cleanup_worker()
        self._course_list.clear()
        self._course_status_label.setText("과목 목록을 불러오는 중... (브라우저가 열립니다)")
        self._course_loading_bar.setVisible(True)
        self._set_course_page_enabled(False)

        self._worker = CourseListWorker(self._username, self._password)
        self._worker.courses_loaded.connect(self._on_courses_loaded)
        self._worker.error_occurred.connect(self._on_load_error)
        self._worker.finished_signal.connect(self._on_worker_finished)
        self._worker.start()

    def _on_courses_loaded(self, courses: List[Course]):
        self._courses = courses
        self._course_loading_bar.setVisible(False)
        # 캐시 저장
        save_course_cache([c.to_dict() for c in courses])
        self._populate_course_list()

    def _populate_course_list(self):
        self._course_list.clear()
        for course in self._courses:
            icon_name = "star" if course.is_favorited else "star_outline"
            text = f"{course.long_name}"
            if course.term:
                text += f"  ({course.term})"

            item = QListWidgetItem(text)
            item.setIcon(AppIcons.icon(icon_name))
            item.setData(Qt.UserRole, course)
            self._course_list.addItem(item)

        self._course_status_label.setText(f"{len(self._courses)}개 과목")
        self._set_course_page_enabled(True)

    def _on_course_double_clicked(self, item: QListWidgetItem):
        course = item.data(Qt.UserRole)
        if course:
            self._start_loading_lectures(course)

    # ── 강의 로딩 ──────────────────────────────────────────────

    def _start_loading_lectures(self, course: Course):
        """과목의 주차별 강의 목록 로드"""
        self._cleanup_worker()
        self._stack.setCurrentIndex(1)
        self._lecture_title.setStyleSheet(StyleSheet.modal_title())
        self.setWindowTitle(f"강의 목록 - {course.long_name}")

        self._lecture_tree.clear()
        self._lecture_status_label.setText("강의 목록을 불러오는 중... (브라우저가 열립니다)")
        self._lecture_loading_bar.setVisible(True)
        self._confirm_btn.setEnabled(False)

        self._worker = CourseListWorker(
            self._username, self._password, course=course
        )
        self._worker.lectures_loaded.connect(self._on_lectures_loaded)
        self._worker.error_occurred.connect(self._on_load_error)
        self._worker.finished_signal.connect(self._on_worker_finished)
        self._worker.start()

    def _on_lectures_loaded(self, detail: CourseDetail):
        self._course_detail = detail
        self._lecture_loading_bar.setVisible(False)
        self._populate_lecture_tree(detail)

    def _populate_lecture_tree(self, detail: CourseDetail):
        self._lecture_tree.blockSignals(True)
        self._lecture_tree.clear()

        video_only = self._video_only_checkbox.isChecked()

        for week in detail.weeks:
            lectures_to_show = week.lectures
            if video_only:
                lectures_to_show = week.video_lectures

            if not lectures_to_show:
                continue

            # 주차 노드
            week_item = QTreeWidgetItem(self._lecture_tree)
            week_item.setText(0, week.title)
            week_item.setFlags(
                week_item.flags() | Qt.ItemIsAutoTristate | Qt.ItemIsUserCheckable
            )
            week_item.setCheckState(0, Qt.Unchecked)

            # 볼드 폰트
            font = week_item.font(0)
            font.setBold(True)
            week_item.setFont(0, font)

            # 강의 아이템 노드
            for lecture in lectures_to_show:
                child = QTreeWidgetItem(week_item)

                # 텍스트: 차시 + 제목 + 길이
                parts = []
                if lecture.lesson_label:
                    parts.append(lecture.lesson_label)
                parts.append(lecture.title)
                if lecture.duration:
                    parts.append(f"({lecture.duration})")

                # 출석 상태
                att_map = {
                    "attendance": "출석",
                    "late": "지각",
                    "absent": "결석",
                }
                att_text = att_map.get(lecture.attendance, "")
                if att_text:
                    parts.append(f"[{att_text}]")

                # 예정 표시
                if lecture.is_upcoming:
                    parts.append("[예정]")

                child.setText(0, "  ".join(parts))

                # 아이콘
                icon_name = _TYPE_ICON_MAP.get(lecture.lecture_type, "list")
                child.setIcon(0, AppIcons.icon(icon_name))

                # 예정 항목: 비활성화 (회색 텍스트, 체크 불가)
                if lecture.is_upcoming:
                    child.setFlags(child.flags() & ~(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled))
                    child.setForeground(0, QColor(Colors.TEXT_LIGHT))
                elif lecture.is_video and lecture.item_url:
                    child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                    child.setCheckState(0, Qt.Unchecked)
                else:
                    child.setFlags(child.flags() & ~Qt.ItemIsUserCheckable)

                child.setData(0, Qt.UserRole, lecture)

            week_item.setExpanded(True)

        self._lecture_tree.blockSignals(False)
        self._update_selection_count()

    # ── 필터/선택 ──────────────────────────────────────────────

    def _apply_video_filter(self):
        if self._course_detail:
            self._populate_lecture_tree(self._course_detail)

    def _select_all(self):
        self._lecture_tree.blockSignals(True)
        root = self._lecture_tree.invisibleRootItem()
        for i in range(root.childCount()):
            week_item = root.child(i)
            week_item.setCheckState(0, Qt.Checked)
        self._lecture_tree.blockSignals(False)
        self._update_selection_count()

    def _deselect_all(self):
        self._lecture_tree.blockSignals(True)
        root = self._lecture_tree.invisibleRootItem()
        for i in range(root.childCount()):
            week_item = root.child(i)
            week_item.setCheckState(0, Qt.Unchecked)
        self._lecture_tree.blockSignals(False)
        self._update_selection_count()

    def _on_tree_item_changed(self, item: QTreeWidgetItem, column: int):
        self._update_selection_count()

    def _update_selection_count(self):
        selected = self._get_checked_lectures()
        total_videos = 0
        if self._course_detail:
            total_videos = len(self._course_detail.all_video_lectures)

        count = len(selected)
        self._lecture_status_label.setText(
            f"{total_videos}개 동영상 중 {count}개 선택"
        )
        self._confirm_btn.setEnabled(count > 0)
        self._confirm_btn.setText(f"선택한 강의 추가 ({count})")

    def _get_checked_lectures(self) -> List[LectureItem]:
        """체크된 강의 아이템 목록 반환"""
        checked = []
        root = self._lecture_tree.invisibleRootItem()
        for i in range(root.childCount()):
            week_item = root.child(i)
            for j in range(week_item.childCount()):
                child = week_item.child(j)
                if child.checkState(0) == Qt.Checked:
                    lecture = child.data(0, Qt.UserRole)
                    if lecture and lecture.item_url:
                        checked.append(lecture)
        return checked

    # ── 네비게이션 ─────────────────────────────────────────────

    def _go_back_to_courses(self):
        self._cleanup_worker()
        self._stack.setCurrentIndex(0)
        self.setWindowTitle("강의 목록")

    def _confirm_selection(self):
        selected = self._get_checked_lectures()
        self._selected_urls = [l.full_url for l in selected]
        self.accept()

    def get_selected_urls(self) -> List[str]:
        return self._selected_urls

    # ── 에러/완료 처리 ─────────────────────────────────────────

    def _on_load_error(self, error_msg: str):
        self._course_loading_bar.setVisible(False)
        self._lecture_loading_bar.setVisible(False)
        if self._stack.currentIndex() == 0:
            self._course_status_label.setText(f"오류: {error_msg}")
            self._set_course_page_enabled(True)
        else:
            self._lecture_status_label.setText(f"오류: {error_msg}")

    def _on_worker_finished(self):
        self._course_loading_bar.setVisible(False)
        self._lecture_loading_bar.setVisible(False)
        if self._stack.currentIndex() == 0:
            self._set_course_page_enabled(True)

    # ── 유틸리티 ───────────────────────────────────────────────

    def _make_divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(StyleSheet.divider())
        return line

    def _set_course_page_enabled(self, enabled: bool):
        self._course_list.setEnabled(enabled)

    def _cleanup_worker(self):
        if self._worker and self._worker.isRunning():
            self._worker.request_cancel()
            self._worker.wait(3000)
        self._worker = None

    def closeEvent(self, event):
        self._cleanup_worker()
        event.accept()
