import { useEffect, useState } from "react";
import { api } from "../../api";
import type { SettingsFieldsProps, Catalog } from "./types";
import { Dropdown } from "../Dropdown";

export function PromptSettings({
  draft,
  change,
  isSaving,
  catalog,
  setDraft,
}: SettingsFieldsProps & {
  catalog: Catalog | null;
  setDraft: (draft: SettingsFieldsProps["draft"]) => void;
}) {
  const [preview, setPreview] = useState("");
  useEffect(() => {
    let isActive = true;
    setPreview("");
    const timer = setTimeout(
      () =>
        api<{ text: string }>("/prompt-preview", {
          method: "POST",
          body: JSON.stringify(draft),
        })
          .then((result) => isActive && setPreview(result.text))
          .catch(() => {}),
      250,
    );
    return () => {
      isActive = false;
      clearTimeout(timer);
    };
  }, [draft]);
  return (
    <fieldset disabled={isSaving}>
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
  );
}
