import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "./api";
import type { Job, SettingsResponse } from "./types";
const attendanceLabels: Record<string, string> = {
  attendance: "출석",
  attended: "출석",
  late: "지각",
  absent: "결석",
  excused: "출석 인정",
  none: "출석 정보 없음",
};
const completionLabels: Record<string, string> = {
  completed: "완료",
  complete: "완료",
  incomplete: "미완료",
};
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
export function LMSPanel({
  settings,
  endStage,
  setEndStage,
  onSubmitted,
  report,
}: {
  settings: SettingsResponse | null;
  endStage: number;
  setEndStage: (n: number) => void;
  onSubmitted: (ids: string[]) => Promise<void>;
  report: (e: unknown) => void;
}) {
  const [tab, setTab] = useState("urls"),
    [urls, setUrls] = useState(""),
    [courses, setCourses] = useState<Cache<Course[]> | null>(null),
    [course, setCourse] = useState(""),
    [detail, setDetail] = useState<Cache<Detail | null> | null>(null),
    [selected, setSelected] = useState<string[]>([]),
    [query, setQuery] = useState<Query | null>(null),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [term, setTerm] = useState("all"),
    [favorites, setFavorites] = useState(false);
  const batch = useRef<{
    sources: { kind: string; reference: string }[];
    settings_revision: string;
    end_stage: number;
    key: string;
  } | null>(null);
  const [uncertain, setUncertain] = useState(false);
  const epoch = useRef(0),
    courseRef = useRef(course);
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
      .then((r) => {
        if (gen === epoch.current) {
          setCourses(r);
          setQuery(r.refresh);
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
      .then((r) => {
        if (alive && gen === epoch.current) {
          setDetail(r);
          setQuery(r.refresh);
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
      } catch (e) {
        if (alive) report(e);
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
    } catch (e) {
      report(e);
    } finally {
      setBusy(false);
    }
  }
  async function submit(references: string[]) {
    if (!settings || (!references.length && !batch.current)) return;
    setBusy(true);
    setMessage("");
    let acknowledged = false;
    try {
      batch.current ??= {
        sources: references.map((reference) => ({ kind: "url", reference })),
        settings_revision: settings.settings_revision,
        end_stage: endStage,
        key: Array.from(crypto.getRandomValues(new Uint8Array(16)), (v) =>
          v.toString(16).padStart(2, "0"),
        ).join(""),
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
    } catch (e) {
      report(e);
      if (e instanceof ApiError && !acknowledged) {
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
  const available =
    detail?.data?.weeks
      .flatMap((w) => w.lectures)
      .filter((l) => l.is_video && !l.is_upcoming) ?? [];
  const urlLines = urls.split(/\s+/).filter(Boolean);
  return (
    <section className="panel lms-panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">FROM YOUR LMS</span>
          <h2>LMS 강의 가져오기</h2>
        </div>
        <div className="artifact-tabs" role="group" aria-label="LMS 입력 방식">
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
        <p className="muted">처리 설정에서 학번·비밀번호를 저장해 주세요.</p>
        <label>
          LMS 마지막 처리 단계
          <select
            value={endStage}
            disabled={busy || uncertain}
            onChange={(e) => setEndStage(Number(e.target.value))}
          >
            <option value={4}>요약 / 프롬프트 준비</option>
            <option value={3}>음성 인식까지만</option>
            <option value={2}>오디오 변환까지만</option>
            <option value={1}>다운로드까지만</option>
          </select>
        </label>
      </div>
      {message && (
        <p role="status" className="manual-note">
          {message}
        </p>
      )}
      {query && ["queued", "running"].includes(query.status) && (
        <p role="status">
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
              onChange={(e) => setUrls(e.target.value)}
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
              onClick={() => void submit(urlLines)}
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
              <select value={term} onChange={(e) => setTerm(e.target.value)}>
                <option value="all">전체 학기</option>
                {[...new Set(courses?.data.map((c) => c.term) ?? [])].map(
                  (t) => (
                    <option key={t}>{t}</option>
                  ),
                )}
              </select>
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
            <select value={course} onChange={(e) => setCourse(e.target.value)}>
              <option value="">과목을 선택하세요</option>
              {courses?.data
                .filter(
                  (c) =>
                    (term === "all" || c.term === term) &&
                    (!favorites || c.is_favorited),
                )
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.is_favorited ? "★ " : ""}
                    {c.long_name} · {c.term}
                  </option>
                ))}
            </select>
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
                  className="quiet"
                  disabled={uncertain}
                  onClick={() =>
                    setSelected([...new Set(available.map((l) => l.url))])
                  }
                >
                  영상 전체 선택
                </button>
                <button
                  className="quiet"
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
              {detail?.data?.weeks.map((w) => (
                <details
                  key={w.week_number + "-" + w.title}
                  className="lecture-week"
                  open
                >
                  <summary>{w.title}</summary>
                  {w.lectures.map((l, i) => (
                    <label className="lecture-row" key={l.url + i}>
                      <input
                        type="checkbox"
                        disabled={uncertain || !l.is_video || l.is_upcoming}
                        checked={selected.includes(l.url)}
                        onChange={(e) =>
                          setSelected(
                            e.target.checked
                              ? [...selected, l.url]
                              : selected.filter((v) => v !== l.url),
                          )
                        }
                      />
                      <span>
                        <strong>{l.title}</strong>
                        <small>
                          {l.duration ?? ""} ·{" "}
                          {attendanceLabels[l.attendance] ?? l.attendance} /{" "}
                          {completionLabels[l.completion] ?? l.completion}{" "}
                          {l.is_upcoming
                            ? "· 예정"
                            : !l.is_video
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
                  onClick={() => void submit(selected)}
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
export function JobLogs({ job }: { job: Job }) {
  const cursor = useRef(0);
  const [logs, setLogs] = useState<
      {
        seq: number;
        type: string;
        timestamp: string;
        message?: string;
        stage?: number;
        status?: string;
        attempt_id?: string;
      }[]
    >([]),
    [error, setError] = useState("");
  useEffect(() => {
    let alive = true;
    setLogs([]);
    setError("");
    cursor.current = 0;
    const load = () =>
      api<{ logs: typeof logs; next_cursor: number }>(
        "/jobs/" + job.id + "/logs?limit=200&cursor=" + cursor.current,
      )
        .then((r) => {
          if (alive) {
            cursor.current = r.next_cursor;
            setLogs((old) =>
              [
                ...old,
                ...r.logs.filter((l) => !old.some((o) => o.seq === l.seq)),
              ].slice(-200),
            );
            setError("");
          }
        })
        .catch(() => alive && setError("로그를 불러오지 못했습니다."));
    void load();
    const timer = setInterval(load, 3000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [job.id]);
  const labels: Record<string, string> = {
    stage_started: "단계 시작",
    stage_completed: "단계 완료",
    queued: "대기",
    running: "실행",
    completed: "완료",
    failed: "실패",
    cancelled: "취소",
    interrupted: "중단",
    cancelling: "취소 요청",
  };
  return (
    <details className="attempt-history">
      <summary>작업 로그 · 최근 200개</summary>
      {error && <p role="status">{error}</p>}
      <ol className="job-logs">
        {logs.map((l) => (
          <li key={l.seq}>
            <time>{new Date(l.timestamp).toLocaleTimeString("ko-KR")}</time>
            <span>
              {l.stage ? "단계 " + l.stage + " · " : ""}
              {labels[l.message ?? l.status ?? ""] ?? l.type}
            </span>
          </li>
        ))}
      </ol>
      {!logs.length && !error && (
        <p>저장된 로그가 없습니다. 로그는 7일 동안 보관합니다.</p>
      )}
    </details>
  );
}
export function ServerPanel({ report }: { report: (e: unknown) => void }) {
  const [system, setSystem] = useState<{
      version: string;
      sqlite_version: string;
      free_bytes: number;
      chrome_available: boolean;
      health: { running: boolean; error_code: string | null };
      stage_counts: Record<string, unknown>;
      runtime: { chrome_mode: string; local_stt_device: string };
    } | null>(null),
    [update, setUpdate] = useState<{
      status: string;
      latest?: string;
      newer?: boolean;
      url?: string;
    } | null>(null),
    [busy, setBusy] = useState(false);
  async function load() {
    try {
      setSystem(await api("/system"));
    } catch (e) {
      report(e);
    }
  }
  useEffect(() => {
    void load();
  }, []);
  async function check() {
    setBusy(true);
    try {
      setUpdate(
        await api("/system/update-check", { method: "POST", body: "{}" }),
      );
    } catch (e) {
      report(e);
    } finally {
      setBusy(false);
    }
  }
  return (
    <details className="panel server-panel">
      <summary>서버 진단·버전·업데이트</summary>
      <div className="diagnostic-grid">
        <div>
          <h3>실행 상태</h3>
          <p>
            버전 {system?.version ?? "확인 중"} · SQLite{" "}
            {system?.sqlite_version ?? "—"}
          </p>
          <p>
            작업 서비스 {system?.health.running ? "실행 중" : "확인 필요"} ·
            Chrome {system?.chrome_available ? "사용 가능" : "경로 확인 필요"}
          </p>
          <p>
            여유 공간{" "}
            {system ? (system.free_bytes / 1024 ** 3).toFixed(1) + " GiB" : "—"}
          </p>
          <button className="quiet" onClick={() => void load()}>
            진단 새로고침
          </button>
        </div>
        <div>
          <h3>서버 실행·저장</h3>
          <p>
            시스템 Chrome · {system?.runtime.chrome_mode ?? "확인 중"} / 로컬
            STT · {system?.runtime.local_stt_device ?? "CPU 기본"}
          </p>
          <p>
            데이터와 모델은 별도 서버 볼륨에 저장합니다. 기기 폴더 열기는 결과
            다운로드로 제공합니다.
          </p>
          <p>
            Chrome 경로·화면 모드는 서버 실행 설정입니다. 접속 기기 경로를
            사용하지 않습니다.
          </p>
        </div>
        <div>
          <h3>업데이트 안내</h3>
          <button
            className="secondary"
            disabled={busy}
            onClick={() => void check()}
          >
            {busy ? "확인 중…" : "최신 릴리즈 확인"}
          </button>
          {update && (
            <p role="status">
              {update.status === "unavailable"
                ? "릴리즈를 확인하지 못했습니다. 나중에 다시 확인해 주세요."
                : update.newer
                  ? `새 버전 ${update.latest}`
                  : `최신 확인: ${update.latest}`}
              {update.url && (
                <>
                  {" "}
                  ·{" "}
                  <a href={update.url} target="_blank" rel="noreferrer">
                    릴리즈 보기 ↗
                  </a>
                </>
              )}
            </p>
          )}
          <p>데이터·모델 볼륨을 백업한 뒤 서버에서 실행하세요.</p>
          <code>docker compose up -d --build</code>
          <p>화면에서 앱을 자동 교체하지 않습니다.</p>
        </div>
      </div>
    </details>
  );
}
