import { useEffect, useState } from "react";
import { api } from "../api";
import type { Settings, SettingsResponse } from "../types";
import { SecretField } from "../components/SecretField";
import { Dropdown } from "../components/Dropdown";
import { Combobox } from "../components/Combobox";

type Model = { id: string; label: string };
type Provider = { default_model: string; models: Model[] };
type Catalog = {
  summary: Record<string, Provider>;
  stt: Record<string, Provider>;
  summary_modes: Record<string, string>;
  subject_categories: string[];
  default_prompt: string;
};

const summaryLabels: Record<string, string> = {
  clipboard: "챗봇에서 직접 요약",
  gemini: "Gemini API",
  openai: "OpenAI API",
  claude: "Claude API",
  grok: "Grok API",
  custom: "OpenAI 호환 API",
};
const sttLabels: Record<string, string> = {
  "faster-whisper": "faster-whisper · 로컬 모델",
  "openai-whisper": "OpenAI Whisper API",
  "openai-compatible": "OpenAI 호환 STT",
  returnzero: "ReturnZero",
};

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

type Playback = {
  id: string;
  title: string;
  status: string;
  attended: boolean;
  error_code: string | null;
  lecture_url: string;
  created_at: string;
};

export function SettingsPage({
  draft,
  setDraft,
  settings,
  onSecrets,
  save,
  saving,
  report,
}: {
  draft: Settings;
  setDraft: (settings: Settings) => void;
  settings: SettingsResponse;
  onSecrets: (settings: SettingsResponse) => void;
  save: () => void;
  saving: boolean;
  report: (cause: unknown) => void;
}) {
  const [secretBusy, setSecretBusy] = useState(0);
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [preview, setPreview] = useState("");
  const [auto, setAuto] = useState<AutoStatus | null>(null);
  const [checking, setChecking] = useState(false);
  const [courses, setCourses] = useState<MiniCourse[]>([]);
  const [playbacks, setPlaybacks] = useState<Playback[]>([]);
  useEffect(() => {
    api<Catalog>("/catalog").then(setCatalog).catch(report);
  }, []);
  useEffect(() => {
    api<AutoStatus>("/auto-detect").then(setAuto).catch(() => {});
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
  const selectedCourses = draft.auto_detect_courses.split(/[\s,]+/).filter(Boolean);
  const toggleCourse = (id: string) =>
    change(
      "auto_detect_courses",
      (selectedCourses.includes(id)
        ? selectedCourses.filter((value) => value !== id)
        : [...selectedCourses, id]
      ).join(","),
    );
  async function checkAutoDetect() {
    setChecking(true);
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
      setChecking(false);
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
  const change = (name: keyof Settings, value: unknown) =>
    setDraft({ ...draft, [name]: value });
  const param = (name: string, value: unknown) =>
    change("stt_params", { ...draft.stt_params, [name]: value });
  useEffect(() => {
    let active = true;
    setPreview("");
    const timer = setTimeout(
      () =>
        api<{ text: string }>("/prompt-preview", {
          method: "POST",
          body: JSON.stringify(draft),
        })
          .then((result) => active && setPreview(result.text))
          .catch(() => {}),
      250,
    );
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [draft]);
  const secret = (name: string, label: string) => (
    <SecretField
      key={name}
      name={name}
      label={label}
      settings={settings}
      onChange={onSecrets}
      report={report}
      disabled={saving}
      onBusy={(busy) => setSecretBusy((count) => count + (busy ? 1 : -1))}
    />
  );

  return (
    <section className="settings-sheet panel">
      <div className="section-heading">
        <div>
          <h2>어떻게 처리할까요?</h2>
        </div>
      </div>
      <fieldset disabled={saving}>
        <legend>LMS 계정</legend>
        <p className="muted">
          과목 조회와 URL 다운로드에 사용합니다. 저장한 비밀번호는 다시 조회하지
          않습니다.
        </p>
        <div className="settings-grid">
          <label>
            학번
            <input
              value={draft.student_id}
              autoComplete="off"
              onChange={(event) => change("student_id", event.target.value)}
            />
          </label>
          {secret("lms_password", "LMS 비밀번호")}
        </div>
      </fieldset>
      <fieldset disabled={saving}>
        <legend>요약</legend>
        <div className="settings-grid">
          <label>
            요약 방식
            <Dropdown
              value={draft.ai_engine}
              onChange={(value) =>
                setDraft({
                  ...draft,
                  ai_engine: value,
                  ai_model: catalog?.summary[value]?.default_model ?? "",
                })
              }
              ariaLabel="요약 방식"
              options={Object.entries(summaryLabels).map(([value, label]) => ({
                value,
                label,
              }))}
            />
          </label>
          <label>
            요약 모델
            <Combobox
              value={draft.ai_model}
              onChange={(value) => change("ai_model", value)}
              ariaLabel="요약 모델"
              placeholder="목록에서 선택하거나 모델 ID 입력"
              options={(catalog?.summary[draft.ai_engine]?.models ?? []).map(
                (model) => ({ value: model.id, label: model.label }),
              )}
            />
          </label>
          {draft.ai_engine !== "clipboard" &&
            secret("summary:" + draft.ai_engine, "요약 API 키")}
          {draft.ai_engine === "custom" && (
            <label>
              요약 API 주소
              <input
                type="url"
                value={draft.base_url}
                placeholder="https://…/v1"
                onChange={(event) => change("base_url", event.target.value)}
              />
              <small>키 없이 사용하는 서버도 지원합니다.</small>
            </label>
          )}
        </div>
      </fieldset>
      <fieldset disabled={saving}>
        <legend>음성 인식</legend>
        <div className="settings-grid">
          <label>
            음성 인식 방식
            <Dropdown
              value={draft.stt_engine}
              onChange={(value) =>
                setDraft({
                  ...draft,
                  stt_engine: value,
                  stt_model: catalog?.stt[value]?.default_model ?? "",
                })
              }
              ariaLabel="음성 인식 방식"
              options={Object.entries(sttLabels).map(([value, label]) => ({
                value,
                label,
              }))}
            />
          </label>
          {draft.stt_engine !== "returnzero" && (
            <label>
              음성 인식 모델
              <Combobox
                value={
                  draft.stt_engine === "openai-compatible"
                    ? draft.stt_compatible_model
                    : draft.stt_model
                }
                onChange={(value) =>
                  change(
                    draft.stt_engine === "openai-compatible"
                      ? "stt_compatible_model"
                      : "stt_model",
                    value,
                  )
                }
                ariaLabel="음성 인식 모델"
                placeholder="목록에서 선택하거나 모델 ID 입력"
                options={(catalog?.stt[draft.stt_engine]?.models ?? []).map(
                  (model) => ({ value: model.id, label: model.label }),
                )}
              />
            </label>
          )}
          {["openai-whisper", "openai-compatible"].includes(draft.stt_engine) &&
            secret("stt:" + draft.stt_engine, "STT API 키")}
          {draft.stt_engine === "openai-compatible" && (
            <label>
              STT API 주소
              <input
                type="url"
                value={draft.stt_base_url}
                onChange={(event) => change("stt_base_url", event.target.value)}
                placeholder="http://서버:포트/v1"
              />
            </label>
          )}
          {draft.stt_engine === "returnzero" && (
            <>
              {secret("returnzero_client_id", "ReturnZero Client ID")}
              {secret("returnzero_client_secret", "ReturnZero Client Secret")}
            </>
          )}
        </div>
        <details open={draft.stt_engine === "faster-whisper"}>
          <summary>음성 인식 고급 설정</summary>
          <div className="settings-grid">
            {draft.stt_engine === "faster-whisper" && (
              <>
                <label>
                  장치
                  <Dropdown
                    value={String(draft.stt_params.device ?? "cpu")}
                    onChange={(value) => param("device", value)}
                    ariaLabel="장치"
                    options={["cpu", "auto", "cuda"].map((value) => ({
                      value,
                      label: value,
                    }))}
                  />
                  <small>
                    기본 Docker 구성은 CPU입니다. CUDA는 호스트·컨테이너 설정이
                    필요합니다.
                  </small>
                </label>
                <label>
                  연산 정밀도
                  <Dropdown
                    value={String(draft.stt_params.compute_type ?? "int8")}
                    onChange={(value) => param("compute_type", value)}
                    ariaLabel="연산 정밀도"
                    options={[
                      "auto",
                      "int8",
                      "float16",
                      "float32",
                      "int8_float16",
                    ].map((value) => ({ value, label: value }))}
                  />
                </label>
                <label>
                  언어 코드
                  <input
                    value={String(draft.stt_params.language ?? "ko")}
                    onChange={(event) => param("language", event.target.value)}
                    placeholder="ko / en"
                  />
                </label>
                <label>
                  인식 힌트
                  <textarea
                    rows={3}
                    value={String(
                      draft.stt_params.initial_prompt ?? "한국어 강의입니다.",
                    )}
                    onChange={(event) =>
                      param("initial_prompt", event.target.value)
                    }
                  />
                </label>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={Boolean(draft.stt_params.vad_filter ?? true)}
                    onChange={(event) =>
                      param("vad_filter", event.target.checked)
                    }
                  />
                  무음 구간 감지 (VAD)
                </label>
              </>
            )}
            <label>
              반복 제거 기준
              <input
                type="number"
                min={1}
                max={100}
                value={Number(draft.stt_params.repeat_threshold ?? 4)}
                onChange={(event) =>
                  param("repeat_threshold", Number(event.target.value))
                }
              />
            </label>
          </div>
        </details>
      </fieldset>
      <fieldset disabled={saving}>
        <legend>프롬프트</legend>
        <div className="settings-grid">
          <label>
            프롬프트 방식
            <Dropdown
              value={draft.prompt_mode}
              onChange={(value) => change("prompt_mode", value)}
              ariaLabel="프롬프트 방식"
              options={[
                { value: "structured", label: "기본 강의 요약" },
                { value: "custom", label: "직접 작성" },
              ]}
            />
          </label>
          {draft.prompt_mode === "structured" && (
            <>
              <label>
                요약 모드
                <Dropdown
                  value={draft.summary_mode}
                  onChange={(value) => change("summary_mode", value)}
                  ariaLabel="요약 모드"
                  options={Object.entries(
                    catalog?.summary_modes ?? {
                      quick: "빠른 요약",
                      normal: "일반 요약",
                      detailed: "상세 요약",
                    },
                  ).map(([value, label]) => ({ value, label }))}
                />
              </label>
              <label>
                과목 분야
                <Dropdown
                  value={draft.subject_category}
                  onChange={(value) => change("subject_category", value)}
                  ariaLabel="과목 분야"
                  options={(catalog?.subject_categories ?? ["자동 감지"]).map(
                    (value) => ({ value, label: value }),
                  )}
                />
              </label>
              <label>
                과목명·분야 직접 입력
                <input
                  value={draft.subject_custom}
                  onChange={(event) =>
                    change("subject_custom", event.target.value)
                  }
                  placeholder="직접 입력이 선택 분야보다 우선합니다."
                />
              </label>
            </>
          )}
        </div>
        {draft.prompt_mode === "custom" && (
          <label>
            요약 지시문
            <textarea
              rows={8}
              value={draft.custom_prompt}
              onChange={(event) => change("custom_prompt", event.target.value)}
            />
          </label>
        )}
        <button
          type="button"
          className="ghost"
          onClick={() =>
            setDraft({
              ...draft,
              prompt_mode: "structured",
              summary_mode: "normal",
              subject_category: "자동 감지",
              subject_custom: "",
              custom_prompt: catalog?.default_prompt ?? draft.custom_prompt,
            })
          }
        >
          프롬프트 초기화
        </button>
        <details>
          <summary>적용 프롬프트 미리보기</summary>
          <pre className="prompt-preview">
            {preview || "미리보기를 준비하고 있습니다."}
          </pre>
        </details>
      </fieldset>
      <fieldset disabled={saving}>
        <legend>실행 · 보관</legend>
        <div className="settings-grid">
          <label>
            공급자 요청 제한 시간 (초)
            <input
              type="number"
              min={5}
              max={1800}
              value={draft.request_timeout ?? 120}
              onChange={(event) =>
                change("request_timeout", Number(event.target.value))
              }
            />
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={draft.keep_source}
              onChange={(event) => change("keep_source", event.target.checked)}
            />
            처리 후 서버 원본 보관
          </label>
        </div>
        <p className="muted">
          실패·취소·중단 입력은 재시도용으로 보존합니다. 원문·요약·프롬프트와 작업
          이력은 자동 삭제하지 않습니다. 파일은 서버 볼륨에 저장하며 이 기기로
          다운로드할 수 있습니다.
        </p>
      </fieldset>
      <fieldset disabled={saving}>
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
            <small>과목 캐시가 없습니다. 과목·주차에서 목록을 새로고침하세요.</small>
          ) : (
            <div className="course-checks">
              {courses.map((course) => (
                <label key={course.id} className="check">
                  <input
                    type="checkbox"
                    checked={selectedCourses.includes(course.id)}
                    disabled={saving}
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
            disabled={checking}
            onClick={() => void checkAutoDetect()}
          >
            {checking ? "확인 중…" : "지금 확인"}
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
      <div className="form-footer">
        <p>
          자격 증명은 개별 저장·교체합니다. 나머지 변경은 설정 저장 후 새 작업부터
          적용됩니다.
        </p>
        <button className="primary" disabled={saving || secretBusy > 0} onClick={save}>
          {saving ? "저장 중…" : "설정 저장"}
        </button>
      </div>
    </section>
  );
}
