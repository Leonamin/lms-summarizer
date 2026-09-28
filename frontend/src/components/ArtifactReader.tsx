import { useRef } from "react";
import ReactMarkdown from "react-markdown";
import type { Artifact } from "../types";
import { bytes, kindLabels } from "../lib/format";

export function ArtifactReader({
  artifact,
  text,
  loading,
  onNotice,
}: {
  artifact: Artifact;
  text: string;
  loading: boolean;
  onNotice: (message: string) => void;
}) {
  const textArea = useRef<HTMLTextAreaElement>(null);

  const copy = async () => {
    try {
      if (!navigator.clipboard) throw new Error("manual");
      await navigator.clipboard.writeText(text);
      onNotice("클립보드에 복사했습니다.");
    } catch {
      textArea.current?.focus();
      textArea.current?.select();
      onNotice("텍스트를 전체 선택했습니다. 기기의 복사 기능을 사용해 주세요.");
    }
  };

  return (
    <div className="reader">
      <div className="reader-toolbar">
        <span>
          {kindLabels[artifact.kind] ?? artifact.kind} · {bytes(artifact.size)}
        </span>
        <div>
          <button
            className="ghost"
            disabled={loading || !text}
            onClick={() => void copy()}
          >
            복사
          </button>
          <a
            className="ghost"
            href={"/api/v1/artifacts/" + artifact.id + "/download"}
            download
          >
            다운로드 ↓
          </a>
        </div>
      </div>
      {loading ? (
        <p className="reader-empty" role="status">
          결과를 불러오는 중…
        </p>
      ) : artifact.kind === "summary" ? (
        <div className="markdown">
          <ReactMarkdown>{text}</ReactMarkdown>
        </div>
      ) : null}
      <label
        className={artifact.kind === "summary" ? "sr-only" : ""}
        htmlFor="result-text"
      >
        {artifact.kind === "summary"
          ? "요약 원문"
          : "원문 · 전체 선택하여 복사할 수 있습니다."}
      </label>
      <textarea
        id="result-text"
        ref={textArea}
        className={artifact.kind === "summary" ? "source-text" : "result-text"}
        readOnly
        value={text}
        rows={12}
      />
    </div>
  );
}
