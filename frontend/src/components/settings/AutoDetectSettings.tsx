import { useEffect, useState } from "react";
import { api } from "../../api";
import type { Playback } from "../../types";
import type { SettingsFieldsProps } from "./types";
import { Dropdown } from "../Dropdown";
type AutoStatus = {
  enabled: boolean;
  interval_minutes: number;
  courses: string[];
  scope: string;
  paused: boolean;
  last_run: string | null;
  last_error: string | null;
  detected: number;
  playing: number;
};

type MiniCourse = { id: string; long_name: string; term: string };

export function AutoDetectSettings({
  draft,
  change,
  isSaving,
  report,
}: SettingsFieldsProps & { report: (cause: unknown) => void }) {
  const [auto, setAuto] = useState<AutoStatus | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [courses, setCourses] = useState<MiniCourse[]>([]);
  const [playbacks, setPlaybacks] = useState<Playback[]>([]);
  useEffect(() => {
    api<AutoStatus>("/auto-detect")
      .then(setAuto)
      .catch(() => {});
    api<{ data: MiniCourse[] }>("/courses")
      .then((result) => setCourses(result.data ?? []))
      .catch(() => {});
  }, []);
  const loadPlaybacks = () =>
    api<{ records: Playback[] }>("/playback")
      .then((result) => setPlaybacks([...result.records].reverse().slice(0, 5)))
      .catch(() => {});
  useEffect(() => {
    void loadPlaybacks();
  }, []);
  const selectedCourses = draft.auto_detect_courses
    .split(/[\s,]+/)
    .filter(Boolean);
  const toggleCourse = (id: string) =>
    change(
      "auto_detect_courses",
      (selectedCourses.includes(id)
        ? selectedCourses.filter((value) => value !== id)
        : [...selectedCourses, id]
      ).join(","),
    );
  async function checkAutoDetect() {
    setIsChecking(true);
    try {
      setAuto(
        await api<AutoStatus>("/auto-detect/check", {
          method: "POST",
          body: "{}",
        }),
      );
      void loadPlaybacks();
    } catch (cause) {
      report(cause);
    } finally {
      setIsChecking(false);
    }
  }
  async function resumeAutoDetect() {
    try {
      setAuto(
        await api<AutoStatus>("/auto-detect/resume", {
          method: "POST",
          body: "{}",
        }),
      );
      void loadPlaybacks();
    } catch (cause) {
      report(cause);
    }
  }
  return (
    <fieldset disabled={isSaving}>
      <legend>자동 감지 · 자동 저장</legend>
      <p className="muted">
        켠 동안에만 선택 과목의 신규 영상을 설정 주기로 감지해 자동 저장합니다.
        출석을 위한 자동 재생은 후속 단계입니다.
      </p>
      <div className="settings-grid">
        <label className="check">
          <input
            type="checkbox"
            checked={draft.auto_detect_enabled}
            onChange={(event) =>
              change("auto_detect_enabled", event.target.checked)
            }
          />
          자동 감지 사용
        </label>
        <label>
          감지 주기 (분)
          <input
            type="number"
            min={5}
            max={1440}
            value={draft.auto_detect_interval_minutes ?? 30}
            onChange={(event) =>
              change("auto_detect_interval_minutes", Number(event.target.value))
            }
          />
        </label>
        <label>
          자동 저장 범위
          <Dropdown
            value={draft.auto_save_scope}
            onChange={(value) => change("auto_save_scope", value)}
            ariaLabel="자동 저장 범위"
            options={[
              { value: "download", label: "다운로드만" },
              { value: "full", label: "다운로드 + STT + 요약" },
            ]}
          />
        </label>
      </div>
      <div className="auto-courses">
        <span className="auto-courses-title">감지할 과목</span>
        {courses.length === 0 ? (
          <small>
            과목 캐시가 없습니다. 과목·주차에서 목록을 새로고침하세요.
          </small>
        ) : (
          <div className="course-checks">
            {courses.map((course) => (
              <label key={course.id} className="check">
                <input
                  type="checkbox"
                  checked={selectedCourses.includes(course.id)}
                  disabled={isSaving}
                  onChange={() => toggleCourse(course.id)}
                />
                <span>
                  {course.long_name} · {course.term}
                </span>
              </label>
            ))}
          </div>
        )}
      </div>
      {draft.auto_detect_enabled && (
        <p className="muted">
          자동 재생은 서버에서 Xvfb로 headed 실행됩니다(영상 재생을 위해 필요).
        </p>
      )}
      {playbacks.length > 0 && (
        <ul className="playback-list">
          {playbacks.map((item) => (
            <li key={item.id}>
              <span
                className={
                  "status " + (item.attended ? "completed" : item.status)
                }
              >
                {item.attended ? "출석 완료" : item.status}
              </span>
              <span className="playback-title">
                {item.title || item.lecture_url}
              </span>
              {item.error_code && (
                <small className="muted">{item.error_code}</small>
              )}
            </li>
          ))}
        </ul>
      )}
      <div className="auto-status">
        <button
          type="button"
          className="ghost"
          disabled={isChecking}
          onClick={() => void checkAutoDetect()}
        >
          {isChecking ? "확인 중…" : "지금 확인"}
        </button>
        {auto && (
          <span className="muted">
            감지 {auto.detected}건 · 재생 {auto.playing}건 ·{" "}
            {auto.paused
              ? "일시중지"
              : auto.last_error
                ? "오류: " + auto.last_error
                : "정상"}
            {auto.last_run
              ? " · 최근 " + new Date(auto.last_run).toLocaleString("ko-KR")
              : ""}
          </span>
        )}
        {auto?.paused && (
          <button
            type="button"
            className="secondary"
            onClick={() => void resumeAutoDetect()}
          >
            재개
          </button>
        )}
      </div>
    </fieldset>
  );
}
