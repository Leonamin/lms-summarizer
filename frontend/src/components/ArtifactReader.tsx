import { useEffect, useRef, useState } from "react";
import type { Artifact } from "../types";
import { bytes, kindLabels } from "../lib/format";
import { ArtifactBody } from "./ArtifactBody";

/** Clipboard write with a legacy textarea fallback for insecure contexts. */
async function copyText(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    /* fall through to the legacy path */
  }
  try {
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(area);
    return ok;
  } catch {
    return false;
  }
}

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
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [expanded, setExpanded] = useState(false);
  const label = kindLabels[artifact.kind] ?? artifact.kind;
  const download = "/api/v1/artifacts/" + artifact.id + "/download";

  // Close the full-screen viewer when the displayed artifact changes.
  useEffect(() => {
    if (dialogRef.current?.open) dialogRef.current.close();
    setExpanded(false);
  }, [artifact.id]);

  // Native <dialog> gives focus trapping and Escape handling for free.
  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog && expanded && !dialog.open) dialog.showModal();
  }, [expanded]);

  const copy = async () => {
    onNotice(
      (await copyText(text))
        ? "클립보드에 복사했습니다."
        : "복사하지 못했습니다. 본문을 직접 선택해 주세요.",
    );
  };

  return (
    <div className="reader">
      <div className="reader-toolbar">
        <span>
          {label} · {bytes(artifact.size)}
        </span>
        <div>
          <button
            className="ghost"
            disabled={loading || !text}
            onClick={() => setExpanded(true)}
          >
            전체 보기
          </button>
          <button
            className="ghost"
            disabled={loading || !text}
            onClick={() => void copy()}
          >
            복사
          </button>
          <a className="ghost" href={download} download>
            다운로드 ↓
          </a>
        </div>
      </div>
      {loading ? (
        <p className="reader-empty" role="status">
          결과를 불러오는 중…
        </p>
      ) : (
        <div className="reader-body">
          <ArtifactBody artifact={artifact} text={text} inputId="result-text" />
        </div>
      )}
      <dialog
        ref={dialogRef}
        className="viewer-dialog"
        aria-label={label + " 전체 보기"}
        onClose={() => setExpanded(false)}
        onClick={(event) => {
          if (event.target === dialogRef.current) dialogRef.current?.close();
        }}
      >
        <div className="viewer-head">
          <span>
            {label} · {bytes(artifact.size)}
          </span>
          <div>
            <button
              className="ghost"
              disabled={!text}
              onClick={() => void copy()}
            >
              복사
            </button>
            <a className="ghost" href={download} download>
              다운로드 ↓
            </a>
            <button
              className="ghost"
              aria-label="뷰어 닫기"
              onClick={() => dialogRef.current?.close()}
            >
              닫기 ✕
            </button>
          </div>
        </div>
        <div className="viewer-body">
          <ArtifactBody artifact={artifact} text={text} inputId="viewer-text" />
        </div>
      </dialog>
    </div>
  );
}
