import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api";
import type { SettingsResponse } from "../types";
import {
  attendanceLabels,
  completionLabels,
  requestId,
} from "../lib/format";
import { Dropdown } from "./Dropdown";

const endStageOptions = [
  { value: "4", label: "요약 / 프롬프트 준비" },
  { value: "3", label: "음성 인식까지만" },
  { value: "2", label: "오디오 변환까지만" },
  { value: "1", label: "다운로드까지만" },
];

type Course = {
  id: string;
  long_name: string;
  term: string;
  is_favorited: boolean;
};
type Lecture = {
  title: string;
  url: string;
  duration: string | null;
  attendance: string;
  completion: string;
  is_video: boolean;
  is_upcoming: boolean;
  type: string;
};
type Detail = {
  course_name: string;
  professors: string;
  weeks: { title: string; week_number: number; lectures: Lecture[] }[];
};
type Query = {
  id: string;
  status: string;
  error_code: string | null;
  course_id: string | null;
};
type Cache<T> = {
  data: T;
  cache_age_seconds: number | null;
  expired: boolean;
  refresh: Query | null;
};

export function LmsImportPanel({
  settings,
  endStage,
  setEndStage,
  onSubmitted,
  report,
}: {
  settings: SettingsResponse | null;
  endStage: number;
  setEndStage: (stage: number) => void;
  onSubmitted: (ids: string[]) => Promise<void>;
  report: (cause: unknown) => void;
}) {
  const [tab, setTab] = useState("urls");
  const [urls, setUrls] = useState("");
  const [courses, setCourses] = useState<Cache<Course[]> | null>(null);
  const [course, setCourse] = useState("");
  const [detail, setDetail] = useState<Cache<Detail | null> | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [query, setQuery] = useState<Query | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [term, setTerm] = useState("all");
  const [favorites, setFavorites] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const batch = useRef<{
    sources: { kind: string; reference: string }[];
    settings_revision: string;
    end_stage: number;
    key: string;
  } | null>(null);
  const epoch = useRef(0);
  const courseRef = useRef(course);
  courseRef.current = course;

  useEffect(() => {
    epoch.current++;
    setCourses(null);
    setDetail(null);
    setCourse("");
    setSelected([]);
    setQuery(null);
    const gen = epoch.current;
    api<Cache<Course[]>>("/courses")
      .then((result) => {
        if (gen === epoch.current) {
          setCourses(result);
          setQuery(result.refresh);
        }
      })
      .catch(report);
  }, [settings?.settings.student_id, settings?.revision]);

  useEffect(() => {
    setDetail(null);
    setSelected([]);
    if (!course) return;
    let alive = true;
    const gen = epoch.current;
    api<Cache<Detail | null>>("/courses/" + course + "/lectures")
      .then((result) => {
        if (alive && gen === epoch.current) {
          setDetail(result);
          setQuery(result.refresh);
        }
      })
      .catch(report);
    return () => {
      alive = false;
    };
  }, [course]);

  useEffect(() => {
    if (!query || !["queued", "running"].includes(query.status)) return;
    let alive = true;
    const gen = epoch.current;
    const poll = async () => {
      try {
        const result = await api<Query>("/course-refreshes/" + query.id);
        if (!alive || gen !== epoch.current) return;
        setQuery(result);
        if (result.status === "completed") {
          if (result.course_id) {
            const cache = await api<Cache<Detail | null>>(
              "/courses/" + result.course_id + "/lectures",
            );
            if (gen === epoch.current && result.course_id === courseRef.current)
              setDetail(cache);
          } else {
            const cache = await api<Cache<Course[]>>("/courses");
            if (gen === epoch.current) setCourses(cache);
          }
          if (gen === epoch.current) setMessage("목록을 갱신했습니다.");
        } else if (["failed", "interrupted"].includes(result.status))
          setMessage(
            "조회가 " +
              (result.status === "interrupted" ? "중단" : "실패") +
              "되었습니다. 계정·Chrome 진단을 확인한 뒤 다시 갱신해 주세요. (" +
              result.error_code +
              ")",
          );
      } catch (cause) {
        if (alive) report(cause);
      }
    };
    const timer = setInterval(() => void poll(), 1000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [query?.id, query?.status, course]);

  async function refresh(id: string | null) {
    setBusy(true);
    try {
      setQuery(
        await api<Query>("/course-refreshes", {
          method: "POST",
          body: JSON.stringify({ course_id: id }),
        }),
      );
      setMessage("다운로드 단계 사이에서 목록을 조회합니다.");
    } catch (cause) {
      report(cause);
    } finally {
      setBusy(false);
    }
  }

  async function submit(
    items: {
      reference: string;
      display_name?: string;
      course_name?: string;
      week_title?: string;
    }[],
  ) {
    if (!settings || (!items.length && !batch.current)) return;
    setBusy(true);
    setMessage("");
    let acknowledged = false;
    try {
      batch.current ??= {
        sources: items.map((item) => ({ kind: "url", ...item })),
        settings_revision: settings.settings_revision,
        end_stage: endStage,
        key: requestId(),
      };
      const { key, ...body } = batch.current;
      const result = await api<{ job_ids: string[] }>("/jobs", {
        method: "POST",
        body: JSON.stringify(body),
        headers: { "Idempotency-Key": key },
      });
      acknowledged = true;
      await onSubmitted(result.job_ids);
      batch.current = null;
      setUncertain(false);
      setSelected([]);
      setUrls("");
      setMessage(result.job_ids.length + "개 URL 작업을 추가했습니다.");
    } catch (cause) {
      report(cause);
      if (cause instanceof ApiError && !acknowledged) {
        batch.current = null;
        setUncertain(false);
      } else {
        setUncertain(true);
        setMessage(
          "제출 응답을 확인하지 못했습니다. 같은 요청으로 다시 확인해 주세요.",
        );
      }
    } finally {
      setBusy(false);
    }
  }

  function courseSources() {
    const weeks = detail?.data?.weeks ?? [];
    const courseName = detail?.data?.course_name ?? "";
    const map = new Map(
      weeks.flatMap((week) =>
        week.lectures.map(
          (lecture) =>
            [
              lecture.url,
              {
                display_name: lecture.title,
                course_name: courseName,
                week_title: week.title,
              },
            ] as const,
        ),
      ),
    );
    return selected.map((url) => ({ reference: url, ...(map.get(url) ?? {}) }));
  }

  const available =
    detail?.data?.weeks
      .flatMap((week) => week.lectures)
      .filter((lecture) => lecture.is_video && !lecture.is_upcoming) ?? [];
  const urlLines = urls.split(/\s+/).filter(Boolean);

  return (
    <section className="panel lms-panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">FROM YOUR LMS</span>
          <h2>LMS 강의 가져오기</h2>
        </div>
        <div className="segmented" role="group" aria-label="LMS 입력 방식">
          <button
            className={tab === "urls" ? "active" : ""}
            onClick={() => setTab("urls")}
          >
            URL 입력
          </button>
          <button
            className={tab === "courses" ? "active" : ""}
            onClick={() => setTab("courses")}
          >
            과목·주차
          </button>
        </div>
      </div>
      <div className="course-tools">
        <p className="muted" style={{ flex: 1 }}>
          처리 설정에서 학번·비밀번호를 저장해 주세요.
        </p>
        <label>
          LMS 마지막 처리 단계
          <Dropdown
            value={String(endStage)}
            onChange={(value) => setEndStage(Number(value))}
            options={endStageOptions}
            ariaLabel="LMS 마지막 처리 단계"
            disabled={busy || uncertain}
          />
        </label>
      </div>
      {message && (
        <p role="status" className="manual-note">
          {message}
        </p>
      )}
      {query && ["queued", "running"].includes(query.status) && (
        <p role="status" className="muted">
          목록 조회 {query.status === "queued" ? "대기 중" : "실행 중"} ·
          새로고침해도 조회는 계속됩니다.
        </p>
      )}
      {tab === "urls" ? (
        <>
          <label>
            LMS 강의 URL
            <textarea
              rows={3}
              value={urls}
              disabled={busy || uncertain}
              onChange={(event) => setUrls(event.target.value)}
              placeholder="https://canvas.ssu.ac.kr/courses/… (한 줄에 하나)"
            />
          </label>
          <div className="form-footer">
            <small>Canvas LMS URL · 최대 50개 · 실행 중 추가 가능</small>
            <button
              className="primary"
              disabled={
                busy ||
                (!urlLines.length && !uncertain) ||
                urlLines.length > 50 ||
                !settings
              }
              onClick={() => void submit(urlLines.map((reference) => ({ reference })))}
            >
              {busy
                ? "제출 중…"
                : uncertain
                  ? "제출 결과 다시 확인"
                  : urlLines.length + "개 URL 작업 추가"}
            </button>
          </div>
        </>
      ) : (
        <>
          <div className="course-tools">
            <button
              className="secondary"
              disabled={
                busy ||
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
                checked={favorites}
                onChange={(e) => setFavorites(e.target.checked)}
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
                      (!favorites || item.is_favorited),
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
                    busy ||
                    (!!query && ["queued", "running"].includes(query.status))
                  }
                  onClick={() => void refresh(course)}
                >
                  강의 새로고침
                </button>
                <button
                  className="ghost"
                  disabled={uncertain}
                  onClick={() =>
                    setSelected([...new Set(available.map((item) => item.url))])
                  }
                >
                  영상 전체 선택
                </button>
                <button
                  className="ghost"
                  disabled={uncertain}
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
                          uncertain || !lecture.is_video || lecture.is_upcoming
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
                    busy ||
                    (!selected.length && !uncertain) ||
                    selected.length > 50
                  }
                  onClick={() => void submit(courseSources())}
                >
                  {uncertain
                    ? "제출 결과 다시 확인"
                    : selected.length + "개 강의 작업 추가"}
                </button>
              </div>
            </>
          )}
        </>
      )}
    </section>
  );
}
