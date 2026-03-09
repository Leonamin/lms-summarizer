"""
Canvas LMS 과목 목록 및 주차별 강의 목록 스크래퍼

VideoPipeline._setup_browser() 패턴을 재사용하여
Playwright 비동기 브라우저로 Canvas LMS에서 과목/강의 정보를 추출한다.
"""

import asyncio
import re
from typing import List, Optional, Callable

from playwright.async_api import async_playwright, Playwright, Page, Frame

from src.video_pipeline.login import perform_login_if_needed
from src.gui.config.course_models import (
    Course, LectureItem, Week, CourseDetail,
    LectureType, VIDEO_LECTURE_TYPES,
)

_BASE_URL = "https://canvas.ssu.ac.kr"
_DASHBOARD_URL = f"{_BASE_URL}/"
_LECTURES_URL_TEMPLATE = _BASE_URL + "/courses/{course_id}/external_tools/71"

_DEFAULT_CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# xnmb-module_item-icon 클래스 → LectureType 매핑
_TYPE_CLASS_MAP = {
    "movie": LectureType.MOVIE,
    "readystream": LectureType.READYSTREAM,
    "screenlecture": LectureType.SCREENLECTURE,
    "everlec": LectureType.EVERLEC,
    "zoom": LectureType.ZOOM,
    "mp4": LectureType.MP4,
    "assignment": LectureType.ASSIGNMENT,
    "wiki_page": LectureType.WIKI_PAGE,
    "quiz": LectureType.QUIZ,
    "discussion": LectureType.DISCUSSION,
    "file": LectureType.FILE,
    "attachment": LectureType.FILE,
}


class CourseScraper:
    """Canvas LMS 과목/강의 스크래퍼"""

    def __init__(self, username: str, password: str,
                 chrome_path: str = None,
                 headless: bool = False,
                 log_callback: Optional[Callable[[str], None]] = None):
        self.username = username
        self.password = password
        self.chrome_path = chrome_path or _DEFAULT_CHROME_PATH
        self.headless = headless
        self._log = log_callback or (lambda msg: None)
        self._pw = None
        self._browser = None
        self._page = None

    async def _setup_browser(self, playwright: Playwright):
        """브라우저 설정 (VideoPipeline._setup_browser 패턴)"""
        browser = await playwright.chromium.launch(
            headless=self.headless,
            executable_path=self.chrome_path,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--enable-proprietary-codecs",
                "--disable-web-security",
                "--use-fake-ui-for-media-stream",
            ],
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            permissions=["camera", "microphone", "geolocation"],
        )

        page = await context.new_page()
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            window.chrome = { runtime: {} };
        """)

        return page, browser

    async def _ensure_logged_in(self):
        """대시보드로 이동 후 로그인 처리"""
        self._log("LMS에 접속 중...")
        await self._page.goto(_DASHBOARD_URL, wait_until="networkidle")

        if "login" in self._page.url:
            self._log("로그인 진행 중...")
            result = await perform_login_if_needed(
                self._page, self.username, self.password
            )
            if not result:
                raise RuntimeError("LMS 로그인 실패. 학번/비밀번호를 확인하세요.")
            self._log("로그인 완료")
        else:
            self._log("이미 로그인 상태")

    # ── 과목 목록 ──────────────────────────────────────────────

    async def fetch_courses(self) -> List[Course]:
        """대시보드에서 수강 과목 목록 추출"""
        # 대시보드가 아닌 경우 이동
        if "canvas.ssu.ac.kr" not in self._page.url or "/courses/" in self._page.url:
            await self._page.goto(_DASHBOARD_URL, wait_until="networkidle")

        raw = await self._page.evaluate(
            "() => window.ENV && window.ENV.STUDENT_PLANNER_COURSES"
        )

        if not raw:
            raise RuntimeError(
                "과목 목록을 불러올 수 없습니다. 페이지를 확인하세요."
            )

        courses = []
        for item in raw:
            courses.append(Course(
                id=str(item["id"]),
                long_name=item.get("longName", ""),
                href=item.get("href", f"/courses/{item['id']}"),
                term=item.get("term", ""),
                is_favorited=item.get("isFavorited", False),
            ))

        self._log(f"{len(courses)}개 과목 로드 완료")
        return courses

    # ── 주차별 강의 목록 ──────────────────────────────────────

    async def fetch_lectures(self, course: Course) -> CourseDetail:
        """과목의 주차별 강의 목록 페이지를 파싱"""
        url = _LECTURES_URL_TEMPLATE.format(course_id=course.id)
        self._log(f"강의 목록 로딩: {course.long_name}")
        await self._page.goto(url, wait_until="networkidle")

        # tool_content iframe 대기
        iframe_el = await self._page.wait_for_selector(
            "iframe#tool_content", timeout=15000
        )
        iframe = await iframe_el.content_frame()
        if not iframe:
            raise RuntimeError("tool_content iframe을 찾을 수 없습니다.")

        # LTI 콘텐츠 로드 대기
        await iframe.wait_for_selector("#root", timeout=15000)
        await asyncio.sleep(0.5)  # 렌더링 안정화

        # 메타데이터 추출
        root = await iframe.query_selector("#root")
        course_name = await root.get_attribute("data-course_name") or course.long_name
        professors = await root.get_attribute("data-professors") or ""

        # 전체 펼치기
        expand_btn = await iframe.query_selector(".xnmb-all_fold-btn")
        if expand_btn:
            btn_text = await expand_btn.text_content()
            if btn_text and "펼치기" in btn_text:
                await expand_btn.click()
                await asyncio.sleep(0.5)

        # 주차 파싱
        weeks = await self._parse_weeks(iframe)

        total_items = sum(len(w.lectures) for w in weeks)
        total_videos = sum(len(w.video_lectures) for w in weeks)
        self._log(f"{len(weeks)}개 주차, {total_items}개 항목 ({total_videos}개 동영상) 파싱 완료")

        return CourseDetail(
            course=course,
            course_name=course_name,
            professors=professors,
            weeks=weeks,
        )

    async def _parse_weeks(self, iframe: Frame) -> List[Week]:
        """모든 주차 모듈 파싱"""
        # 주차 래퍼들은 .xnmb-module-list 직계 자식 div들
        # 각 div는 .xnmb-module-outer-wrapper(헤더) + 아이템 컨테이너로 구성
        module_list = await iframe.query_selector(".xnmb-module-list")
        if not module_list:
            return []

        # 주차 모듈의 상위 div들 (헤더 div 제외)
        top_divs = await module_list.query_selector_all(":scope > div")

        weeks = []
        for div in top_divs:
            # 주차 헤더가 있는 div인지 확인
            header = await div.query_selector(".xnmb-module-outer-wrapper")
            if not header:
                continue

            # 주차 제목
            title_el = await header.query_selector(".xnmb-module-title")
            title = (await title_el.text_content()).strip() if title_el else ""

            week_num = len(weeks) + 1
            match = re.search(r'(\d+)주차', title)
            if match:
                week_num = int(match.group(1))

            # 아이템들은 header의 sibling div 안에 있음
            items = await div.query_selector_all(
                ".xnmb-module_item-outer-wrapper"
            )

            lectures = []
            for item_el in items:
                lecture = await self._parse_item(item_el)
                if lecture:
                    lectures.append(lecture)

            weeks.append(Week(
                title=title,
                week_number=week_num,
                lectures=lectures,
            ))

        return weeks

    async def _parse_item(self, el) -> Optional[LectureItem]:
        """개별 강의 아이템 파싱"""
        # 타입 판별
        icon_el = await el.query_selector("i.xnmb-module_item-icon")
        lecture_type = LectureType.OTHER
        if icon_el:
            classes = await icon_el.get_attribute("class") or ""
            for cls_name, lt in _TYPE_CLASS_MAP.items():
                if cls_name in classes.split():
                    lecture_type = lt
                    break

        # 제목 & URL
        title_el = await el.query_selector("a.xnmb-module_item-left-title")
        if not title_el:
            # 링크 없는 아이템 (제목만 있는 경우)
            title_el = await el.query_selector(
                ".xnmb-module_item-left-title"
            )
            if not title_el:
                return None
            title = (await title_el.text_content() or "").strip()
            item_url = ""
        else:
            title = (await title_el.text_content() or "").strip()
            item_url = await title_el.get_attribute("href") or ""
            # return_url 파라미터 제거
            if "?" in item_url:
                item_url = item_url.split("?")[0]

        if not title:
            return None

        # 영상 길이
        duration = None
        periods_el = await el.query_selector(
            "[class*='lecture_periods']"
        )
        if periods_el:
            spans = await periods_el.query_selector_all("span")
            for span in reversed(spans):
                text = (await span.text_content() or "").strip()
                if re.match(r'^\d+:\d+$', text):
                    duration = text
                    break

        # 주차/차시
        week_label = ""
        lesson_label = ""
        content_type_label = ""

        week_span = await el.query_selector(
            "[class*='lesson_periods-week']"
        )
        if week_span:
            week_label = (await week_span.text_content() or "").strip()

        lesson_span = await el.query_selector(
            "[class*='lesson_periods-lesson']"
        )
        if lesson_span:
            lesson_label = (await lesson_span.text_content() or "").strip()

        type_span = await el.query_selector(
            "[class*='lesson_periods-dates'] span"
        )
        if type_span:
            content_type_label = (await type_span.text_content() or "").strip()

        # 출석 상태
        attendance = "none"
        att_el = await el.query_selector("[class*='attendance_status']")
        if att_el:
            att_classes = await att_el.get_attribute("class") or ""
            for status in ("attendance", "late", "absent", "excused"):
                if status in att_classes:
                    attendance = status
                    break

        # 완료 상태
        completion = "incomplete"
        comp_el = await el.query_selector("[class*='module_item-completed']")
        if comp_el:
            comp_classes = await comp_el.get_attribute("class") or ""
            if "completed" in comp_classes and "incomplete" not in comp_classes:
                completion = "completed"

        # 예정 상태 (아직 공개되지 않은 강의)
        is_upcoming = False
        dday_el = await el.query_selector(".xncb-component-sub-d_day")
        if dday_el:
            dday_classes = await dday_el.get_attribute("class") or ""
            if "upcoming" in dday_classes:
                is_upcoming = True

        return LectureItem(
            title=title,
            item_url=item_url,
            lecture_type=lecture_type,
            week_label=week_label,
            lesson_label=lesson_label,
            duration=duration,
            attendance=attendance,
            completion=completion,
            content_type_label=content_type_label,
            is_upcoming=is_upcoming,
        )

    # ── 수명 관리 ──────────────────────────────────────────────

    async def start(self):
        """브라우저 시작 및 로그인"""
        self._pw = await async_playwright().start()
        self._page, self._browser = await self._setup_browser(self._pw)
        await self._ensure_logged_in()

    async def close(self):
        """브라우저 종료"""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._pw:
            await self._pw.stop()
            self._pw = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.close()
