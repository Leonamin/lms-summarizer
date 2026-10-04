import type { SettingsFieldsProps, Catalog, SecretRenderer } from "./types";
import { Dropdown } from "../Dropdown";
import { Combobox } from "../Combobox";
const sttLabels: Record<string, string> = {
  "faster-whisper": "faster-whisper · 로컬 모델",
  "openai-whisper": "OpenAI Whisper API",
  "openai-compatible": "OpenAI 호환 STT",
  returnzero: "ReturnZero",
};

export function SpeechSettings({
  draft,
  change,
  isSaving,
  secret,
  catalog,
  setDraft,
}: SettingsFieldsProps & {
  secret: SecretRenderer;
  catalog: Catalog | null;
  setDraft: (draft: SettingsFieldsProps["draft"]) => void;
}) {
  const param = (name: string, value: unknown) =>
    change("stt_params", { ...draft.stt_params, [name]: value });
  return (
    <fieldset disabled={isSaving}>
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
  );
}
