"""
Canvas LMS 과목/강의 데이터 모델
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


_BASE_URL = "https://canvas.ssu.ac.kr"


class LectureType(Enum):
    """강의 아이템 타입 (xnmb-module_item-icon 클래스)"""
    MOVIE = "movie"
    READYSTREAM = "readystream"
    SCREENLECTURE = "screenlecture"
    EVERLEC = "everlec"
    ZOOM = "zoom"
    MP4 = "mp4"
    ASSIGNMENT = "assignment"
    WIKI_PAGE = "wiki_page"
    QUIZ = "quiz"
    DISCUSSION = "discussion"
    FILE = "file"
    OTHER = "other"


VIDEO_LECTURE_TYPES = {
    LectureType.MOVIE,
    LectureType.READYSTREAM,
    LectureType.SCREENLECTURE,
    LectureType.EVERLEC,
    LectureType.MP4,
}


@dataclass
class Course:
    """대시보드에서 추출한 수강 과목 정보"""
    id: str
    long_name: str
    href: str
    term: str
    is_favorited: bool = False

    @property
    def full_url(self) -> str:
        return f"{_BASE_URL}{self.href}"

    @property
    def lectures_url(self) -> str:
        return f"{_BASE_URL}/courses/{self.id}/external_tools/71"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "long_name": self.long_name,
            "href": self.href,
            "term": self.term,
            "is_favorited": self.is_favorited,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Course":
        return cls(
            id=data["id"],
            long_name=data["long_name"],
            href=data["href"],
            term=data.get("term", ""),
            is_favorited=data.get("is_favorited", False),
        )


@dataclass
class LectureItem:
    """주차별 강의 내 개별 아이템"""
    title: str
    item_url: str
    lecture_type: LectureType
    week_label: str = ""
    lesson_label: str = ""
    duration: Optional[str] = None
    attendance: str = "none"
    completion: str = "incomplete"
    content_type_label: str = ""
    is_upcoming: bool = False

    @property
    def is_video(self) -> bool:
        return self.lecture_type in VIDEO_LECTURE_TYPES

    @property
    def full_url(self) -> str:
        if self.item_url.startswith("http"):
            return self.item_url
        return f"{_BASE_URL}{self.item_url}"


@dataclass
class Week:
    """주차 모듈 컨테이너"""
    title: str
    week_number: int
    lectures: List[LectureItem] = field(default_factory=list)

    @property
    def video_lectures(self) -> List[LectureItem]:
        return [l for l in self.lectures if l.is_video]


@dataclass
class CourseDetail:
    """과목의 전체 주차별 강의 상세"""
    course: Course
    course_name: str
    professors: str
    weeks: List[Week] = field(default_factory=list)

    @property
    def all_video_lectures(self) -> List[LectureItem]:
        result = []
        for week in self.weeks:
            result.extend(week.video_lectures)
        return result
