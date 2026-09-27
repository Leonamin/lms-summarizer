import { useEffect, useState } from "react";
import { api } from "../api";
import type { Settings, SettingsResponse } from "../types";
import { SecretField } from "../components/SecretField";

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
  useEffect(() => {
    api<Catalog>("/catalog").then(setCatalog).catch(report);
  }, []);
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
            <select
              value={draft.ai_engine}
              onChange={(event) =>
                setDraft({
                  ...draft,
                  ai_engine: event.target.value,
                  ai_model:
                    catalog?.summary[event.target.value]?.default_model ?? "",
                })
              }
            >
              {Object.entries(summaryLabels).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label>
            요약 모델
            <input
              list="summary-models"
              value={draft.ai_model}
              onChange={(event) => change("ai_model", event.target.value)}
              placeholder="목록에서 선택하거나 모델 ID 입력"
            />
            <datalist id="summary-models">
              {catalog?.summary[draft.ai_engine]?.models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.label}
                </option>
              ))}
            </datalist>
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
            <select
              value={draft.stt_engine}
              onChange={(event) =>
                setDraft({
                  ...draft,
                  stt_engine: event.target.value,
                  stt_model: catalog?.stt[event.target.value]?.default_model ?? "",
                })
              }
            >
              {Object.entries(sttLabels).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          {draft.stt_engine !== "returnzero" && (
            <label>
              음성 인식 모델
              <input
                list="stt-models"
                value={
                  draft.stt_engine === "openai-compatible"
                    ? draft.stt_compatible_model
                    : draft.stt_model
                }
                onChange={(event) =>
                  change(
                    draft.stt_engine === "openai-compatible"
                      ? "stt_compatible_model"
                      : "stt_model",
                    event.target.value,
                  )
                }
              />
              <datalist id="stt-models">
                {catalog?.stt[draft.stt_engine]?.models.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.label}
                  </option>
                ))}
              </datalist>
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
                  <select
                    value={String(draft.stt_params.device ?? "cpu")}
                    onChange={(event) => param("device", event.target.value)}
                  >
                    {["cpu", "auto", "cuda"].map((value) => (
                      <option key={value}>{value}</option>
                    ))}
                  </select>
                  <small>
                    기본 Docker 구성은 CPU입니다. CUDA는 호스트·컨테이너 설정이
                    필요합니다.
                  </small>
                </label>
                <label>
                  연산 정밀도
                  <select
                    value={String(draft.stt_params.compute_type ?? "int8")}
                    onChange={(event) =>
                      param("compute_type", event.target.value)
                    }
                  >
                    {["auto", "int8", "float16", "float32", "int8_float16"].map(
                      (value) => (
                        <option key={value}>{value}</option>
                      ),
                    )}
                  </select>
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
            <select
              value={draft.prompt_mode}
              onChange={(event) => change("prompt_mode", event.target.value)}
            >
              <option value="structured">기본 강의 요약</option>
              <option value="custom">직접 작성</option>
            </select>
          </label>
          {draft.prompt_mode === "structured" && (
            <>
              <label>
                요약 모드
                <select
                  value={draft.summary_mode}
                  onChange={(event) => change("summary_mode", event.target.value)}
                >
                  {Object.entries(
                    catalog?.summary_modes ?? {
                      quick: "빠른 요약",
                      normal: "일반 요약",
                      detailed: "상세 요약",
                    },
                  ).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                과목 분야
                <select
                  value={draft.subject_category}
                  onChange={(event) =>
                    change("subject_category", event.target.value)
                  }
                >
                  {(catalog?.subject_categories ?? ["자동 감지"]).map((value) => (
                    <option key={value}>{value}</option>
                  ))}
                </select>
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
