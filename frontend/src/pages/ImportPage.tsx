import { useState } from "react";
import { BookOpen, Link, Upload } from "lucide-react";
import type { SettingsResponse } from "../types";
import { IntakePanel } from "../components/IntakePanel";
import { LmsImportPanel } from "../components/LmsImportPanel";

const sources = [
  {
    value: "courses",
    label: "과목·주차",
    description: "LMS 목록에서 선택",
    icon: BookOpen,
  },
  {
    value: "urls",
    label: "URL 입력",
    description: "강의 링크로 가져오기",
    icon: Link,
  },
  {
    value: "files",
    label: "파일 업로드",
    description: "영상·오디오·텍스트",
    icon: Upload,
  },
] as const;
type Source = (typeof sources)[number]["value"];

export function ImportPage({
  settings,
  onSubmitted,
  report,
  onSettings,
}: {
  settings: SettingsResponse | null;
  onSubmitted: (ids: string[]) => Promise<void>;
  report: (cause: unknown) => void;
  onSettings: () => void;
}) {
  const [source, setSource] = useState<Source>("courses");
  const [endStage, setEndStage] = useState(4);
  const [fileEndStage, setFileEndStage] = useState(4);
  return (
    <div className="import-page">
      <div className="source-options" role="group" aria-label="가져오기 방식">
        {sources.map(({ value, label, description, icon: Icon }) => (
          <button
            key={value}
            className={"source-option" + (source === value ? " active" : "")}
            aria-pressed={source === value}
            aria-controls="import-content"
            onClick={() => setSource(value)}
          >
            <Icon size={21} aria-hidden="true" />
            <span>
              <strong>{label}</strong>
              <small>{description}</small>
            </span>
          </button>
        ))}
      </div>
      <div id="import-content">
        <div hidden={source === "files"}>
          <LmsImportPanel
            settings={settings}
            mode={source === "urls" ? "urls" : "courses"}
            endStage={endStage}
            setEndStage={setEndStage}
            onSubmitted={onSubmitted}
            report={report}
            onSettings={onSettings}
          />
        </div>
        <div hidden={source !== "files"}>
          <IntakePanel
            settings={settings}
            endStage={fileEndStage}
            setEndStage={setFileEndStage}
            onSubmitted={onSubmitted}
            report={report}
          />
        </div>
      </div>
      <p className="import-hint">
        추가한 작업은 작업실에서 확인할 수 있습니다. 화면을 이동해도 서버의
        처리는 계속됩니다.
      </p>
    </div>
  );
}
