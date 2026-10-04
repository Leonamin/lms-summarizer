import type { SettingsFieldsProps, Catalog, SecretRenderer } from "./types";
import { Dropdown } from "../Dropdown";
import { Combobox } from "../Combobox";
const summaryLabels: Record<string, string> = {
  clipboard: "챗봇에서 직접 요약",
  gemini: "Gemini API",
  openai: "OpenAI API",
  claude: "Claude API",
  grok: "Grok API",
  custom: "OpenAI 호환 API",
};

export function SummarySettings({
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
  return (
    <fieldset disabled={isSaving}>
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
          <>
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
            <label>
              요약 API 호출 방식
              <Dropdown
                value={draft.custom_api_mode ?? "auto"}
                onChange={(value) => change("custom_api_mode", value)}
                ariaLabel="요약 API 호출 방식"
                options={[
                  {
                    value: "auto",
                    label: "자동 (responses → chat/completions)",
                  },
                  { value: "chat", label: "chat/completions" },
                  { value: "responses", label: "responses" },
                ]}
              />
              <small>
                대부분의 OpenAI 호환 서버는 chat/completions를 사용합니다.
              </small>
            </label>
          </>
        )}
      </div>
    </fieldset>
  );
}
