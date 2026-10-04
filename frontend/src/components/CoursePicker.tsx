import { useState } from "react";
import { Dropdown } from "./Dropdown";
import { attendanceLabels, completionLabels } from "../lib/format";
import { getCourseSources, type CourseSource } from "../lib/courses";
import type { useCourseCatalog } from "../hooks/useCourseCatalog";
export function CoursePicker({
  catalog,
  isSubmitting,
  isUncertain,
  hasSettings,
  onSubmit,
}: {
  catalog: ReturnType<typeof useCourseCatalog>;
  isSubmitting: boolean;
  isUncertain: boolean;
  hasSettings: boolean;
  onSubmit: (sources: CourseSource[]) => void;
}) {
  const {
    courses,
    course,
    setCourse,
    detail,
    selected,
    setSelected,
    query,
    refresh,
    isRefreshing,
  } = catalog;
  const isDisabled = isSubmitting || isUncertain || isRefreshing;
  const [term, setTerm] = useState("all");
  const [hasFavoritesFilter, setHasFavoritesFilter] = useState(false);
  const available =
    detail?.data?.weeks
      .flatMap((week) => week.lectures)
      .filter((lecture) => lecture.is_video && !lecture.is_upcoming) ?? [];
  return (
    <>
      <div className="course-tools">
        <button
          className="secondary"
          disabled={
            isDisabled ||
            (!!query && ["queued", "running"].includes(query.status))
          }
          onClick={() => void refresh(null)}
        >
          과목 새로고침
        </button>
        <label>
          학기
          <Dropdown
            value={term}
            onChange={setTerm}
            ariaLabel="학기"
            options={[
              { value: "all", label: "전체 학기" },
              ...[...new Set(courses?.data.map((c) => c.term) ?? [])].map(
                (value) => ({ value, label: value }),
              ),
            ]}
          />
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={hasFavoritesFilter}
            onChange={(e) => setHasFavoritesFilter(e.target.checked)}
          />
          즐겨찾기 과목
        </label>
      </div>
      <p className="muted">
        {courses?.cache_age_seconds != null
          ? "과목 캐시 " +
            Math.floor(courses.cache_age_seconds / 60) +
            "분 전 · 24시간 만료"
          : "저장된 과목이 없습니다."}
        {courses?.expired ? " · 새로고침 필요" : ""}
      </p>
      <label>
        과목 선택
        <Dropdown
          value={course}
          onChange={setCourse}
          ariaLabel="과목 선택"
          options={[
            { value: "", label: "과목을 선택하세요" },
            ...(courses?.data ?? [])
              .filter(
                (item) =>
                  (term === "all" || item.term === term) &&
                  (!hasFavoritesFilter || item.is_favorited),
              )
              .map((item) => ({
                value: item.id,
                label:
                  (item.is_favorited ? "★ " : "") +
                  item.long_name +
                  " · " +
                  item.term,
              })),
          ]}
        />
      </label>
      {course && (
        <>
          <div className="course-tools">
            <button
              className="secondary"
              disabled={
                isDisabled ||
                (!!query && ["queued", "running"].includes(query.status))
              }
              onClick={() => void refresh(course)}
            >
              강의 새로고침
            </button>
            <button
              className="ghost"
              disabled={isDisabled}
              onClick={() =>
                setSelected([...new Set(available.map((item) => item.url))])
              }
            >
              영상 전체 선택
            </button>
            <button
              className="ghost"
              disabled={isDisabled}
              onClick={() => setSelected([])}
            >
              선택 해제
            </button>
          </div>
          <p className="muted">
            {detail?.expired
              ? "강의 캐시가 없거나 만료되었습니다. 새로고침해 주세요."
              : `강의 캐시 ${Math.floor((detail?.cache_age_seconds ?? 0) / 60)}분 전`}
          </p>
          {detail?.data?.weeks.map((week) => (
            <details
              key={week.week_number + "-" + week.title}
              className="lecture-week"
              open
            >
              <summary>{week.title}</summary>
              {week.lectures.map((lecture, index) => (
                <label className="lecture-row" key={lecture.url + index}>
                  <input
                    type="checkbox"
                    disabled={
                      isDisabled || !lecture.is_video || lecture.is_upcoming
                    }
                    checked={selected.includes(lecture.url)}
                    onChange={(event) =>
                      setSelected(
                        event.target.checked
                          ? [...selected, lecture.url]
                          : selected.filter((value) => value !== lecture.url),
                      )
                    }
                  />
                  <span>
                    <strong>{lecture.title}</strong>
                    <small>
                      {lecture.duration ?? ""} ·{" "}
                      {attendanceLabels[lecture.attendance] ??
                        lecture.attendance}{" "}
                      /{" "}
                      {completionLabels[lecture.completion] ??
                        lecture.completion}{" "}
                      {lecture.is_upcoming
                        ? "· 예정"
                        : !lecture.is_video
                          ? "· 영상 아님"
                          : ""}
                    </small>
                  </span>
                </label>
              ))}
            </details>
          ))}
          <div className="form-footer">
            <small>예정 강의·비영상은 선택할 수 없습니다.</small>
            <button
              className="primary"
              disabled={
                isSubmitting ||
                (!selected.length && !isUncertain) ||
                selected.length > 50 ||
                !hasSettings
              }
              onClick={() => onSubmit(getCourseSources(detail?.data, selected))}
            >
              {isUncertain
                ? "제출 결과 다시 확인"
                : selected.length + "개 강의 작업 추가"}
            </button>
          </div>
        </>
      )}
    </>
  );
}
