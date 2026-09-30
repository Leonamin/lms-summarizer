import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import type { Artifact } from "../types";

/** Shared artifact renderer: markdown for summaries, raw selectable text otherwise. */
export function ArtifactBody({
  artifact,
  text,
  inputId,
}: {
  artifact: Artifact;
  text: string;
  inputId: string;
}) {
  if (artifact.kind === "summary") {
    return (
      <div className="markdown">
        <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
          {text}
        </ReactMarkdown>
      </div>
    );
  }
  return (
    <>
      <label className="reader-caption" htmlFor={inputId}>
        원문 · 전체 선택하여 복사할 수 있습니다.
      </label>
      <textarea
        id={inputId}
        className="source-text"
        readOnly
        value={text}
        rows={12}
      />
    </>
  );
}
