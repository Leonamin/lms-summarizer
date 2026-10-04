import { useEffect, useState } from "react";
import { api } from "../api";
import type { Settings, SettingsResponse } from "../types";
import { SecretField } from "../components/SecretField";
import type { Catalog, ChangeSetting } from "../components/settings/types";
import { AccountSettings } from "../components/settings/AccountSettings";
import { SummarySettings } from "../components/settings/SummarySettings";
import { SpeechSettings } from "../components/settings/SpeechSettings";
import { PromptSettings } from "../components/settings/PromptSettings";
import { ExecutionSettings } from "../components/settings/ExecutionSettings";
import { AutoDetectSettings } from "../components/settings/AutoDetectSettings";
/** Key-order-independent JSON so dirty checks survive object rebuilds. */
function stableValue(value: unknown): string {
  return JSON.stringify(value, (_key, item) =>
    item && typeof item === "object" && !Array.isArray(item)
      ? Object.keys(item)
          .sort()
          .reduce<Record<string, unknown>>((sorted, key) => {
            sorted[key] = (item as Record<string, unknown>)[key];
            return sorted;
          }, {})
      : item,
  );
}

export function SettingsPage({
  draft,
  setDraft,
  settings,
  onSecrets,
  save,
  isSaving,
  report,
}: {
  draft: Settings;
  setDraft: (settings: Settings) => void;
  settings: SettingsResponse;
  onSecrets: (settings: SettingsResponse) => void;
  save: () => void;
  isSaving: boolean;
  report: (cause: unknown) => void;
}) {
  const [secretBusy, setSecretBusy] = useState(0);
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  useEffect(() => {
    api<Catalog>("/catalog").then(setCatalog).catch(report);
  }, []);
  const change: ChangeSetting = (name, value) =>
    setDraft({ ...draft, [name]: value });
  const secret = (name: string, label: string) => (
    <SecretField
      key={name}
      name={name}
      label={label}
      settings={settings}
      onChange={onSecrets}
      report={report}
      disabled={isSaving}
      onBusy={(isBusy) => setSecretBusy((count) => count + (isBusy ? 1 : -1))}
    />
  );

  const dirtyFields = (Object.keys(draft) as (keyof Settings)[]).filter(
    (key) => stableValue(draft[key]) !== stableValue(settings.settings[key]),
  );
  const hasChanges = dirtyFields.length > 0;

  return (
    <section className="settings-sheet panel">
      <div className="section-heading">
        <div>
          <h2>어떻게 처리할까요?</h2>
        </div>
      </div>
      <AccountSettings
        draft={draft}
        change={change}
        isSaving={isSaving}
        secret={secret}
      />
      <SummarySettings
        draft={draft}
        change={change}
        isSaving={isSaving}
        secret={secret}
        catalog={catalog}
        setDraft={setDraft}
      />
      <SpeechSettings
        draft={draft}
        change={change}
        isSaving={isSaving}
        secret={secret}
        catalog={catalog}
        setDraft={setDraft}
      />
      <PromptSettings
        draft={draft}
        change={change}
        isSaving={isSaving}
        catalog={catalog}
        setDraft={setDraft}
      />
      <ExecutionSettings draft={draft} change={change} isSaving={isSaving} />
      <AutoDetectSettings
        draft={draft}
        change={change}
        isSaving={isSaving}
        report={report}
      />
      <div className={"form-footer" + (hasChanges ? " unsaved" : "")}>
        <p>
          {hasChanges
            ? `저장되지 않은 변경 ${dirtyFields.length}개가 있습니다. '설정 저장'을 눌러야 새 작업에 적용됩니다.`
            : "자격 증명은 개별 저장·교체합니다. 나머지 변경은 설정 저장 후 새 작업부터 적용됩니다."}
        </p>
        <div className="form-footer-actions">
          {hasChanges && (
            <span className="unsaved-badge">
              미저장 변경 {dirtyFields.length}
            </span>
          )}
          <button
            className="primary"
            disabled={isSaving || secretBusy > 0}
            onClick={save}
          >
            {isSaving ? "저장 중…" : hasChanges ? "변경 저장" : "설정 저장"}
          </button>
        </div>
      </div>
    </section>
  );
}
