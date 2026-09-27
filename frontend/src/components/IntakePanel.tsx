import { useRef, useState } from "react";
import { api, ApiError } from "../api";
import type { SettingsResponse, Upload } from "../types";
import { bytes, requestId } from "../lib/format";

const allowed = /\.(mp4|ts|wav|mp3|txt)$/i;

function stageHint(name: string) {
  if (/\.txt$/i.test(name)) return "요약부터";
  if (/\.(wav|mp3)$/i.test(name)) return "음성 인식부터";
  return "변환부터";
}

export function IntakePanel({
  settings,
  endStage,
  setEndStage,
  onSubmitted,
  report,
}: {
  settings: SettingsResponse | null;
  endStage: number;
  setEndStage: (stage: number) => void;
  onSubmitted: (ids: string[]) => Promise<void>;
  report: (cause: unknown) => void;
}) {
  const [files, setFiles] = useState<File[]>([]);
  const [uploads, setUploads] = useState<Upload[]>([]);
  const [busy, setBusy] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [error, setError] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);
  const batchRef = useRef<{
    uploads: Upload[];
    revision: string;
    endStage: number;
    key: string;
  } | null>(null);

  const addFiles = (list: FileList | null) => {
    if (!list) return;
    const added = Array.from(list);
    if (added.some((file) => !allowed.test(file.name) || file.size === 0)) {
      setError("비어 있지 않은 MP4, TS, WAV, MP3, TXT 파일을 선택해 주세요.");
      return;
    }
    if (added.length + files.length > 50) {
      setError("한 번에 최대 50개 파일을 선택할 수 있습니다.");
      return;
    }
    setFiles((old) => [...old, ...added]);
    setError("");
    if (fileInput.current) fileInput.current.value = "";
  };

  const submit = async () => {
    if (!settings || !files.length) return;
    setBusy(true);
    setError("");
    const staged: Upload[] = batchRef.current?.uploads ?? [];
    let acknowledged = false;
    try {
      const revision = batchRef.current?.revision ?? settings.settings_revision;
      if (!batchRef.current)
        for (const file of files) {
          const reserved = await api<Upload>("/uploads", {
            method: "POST",
            body: JSON.stringify({ filename: file.name, size: file.size }),
          });
          staged.push(reserved);
          setUploads([...staged]);
          try {
            const ready = await api<Upload>(
              "/uploads/" + reserved.id + "/content",
              {
                method: "PUT",
                body: file,
                headers: { "Content-Type": "application/octet-stream" },
              },
            );
            staged[staged.length - 1] = ready;
            setUploads([...staged]);
          } catch (cause) {
            await api("/uploads/" + reserved.id, { method: "DELETE" }).catch(
              () => {},
            );
            throw cause;
          }
        }
      batchRef.current ??= {
        uploads: staged,
        revision,
        endStage,
        key: requestId(),
      };
      const batch = batchRef.current;
      const result = await api<{ job_ids: string[] }>("/jobs", {
        method: "POST",
        headers: { "Idempotency-Key": batch.key },
        body: JSON.stringify({
          sources: batch.uploads.map((item) => ({
            kind: "file",
            reference: item.id,
          })),
          settings_revision: batch.revision,
          end_stage: batch.endStage,
        }),
      });
      acknowledged = true;
      await onSubmitted(result.job_ids);
      batchRef.current = null;
      setUncertain(false);
      setFiles([]);
      setUploads([]);
    } catch (cause) {
      report(cause);
      if (batchRef.current && (!(cause instanceof ApiError) || acknowledged)) {
        setUncertain(true);
        setError(
          "제출 응답을 확인하지 못했습니다. 다시 확인하면 같은 요청을 이어서 조회합니다.",
        );
      } else {
        batchRef.current = null;
        setUncertain(false);
        await Promise.all(
          staged.map((item) =>
            api("/uploads/" + item.id, { method: "DELETE" }).catch(() => {}),
          ),
        );
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="intake panel">
      <div className="intake-title">
        <span className="eyebrow">ADD MATERIAL</span>
        <h2>새로운 강의 자료</h2>
        <p>파일에 맞는 단계부터 이어서 처리합니다.</p>
      </div>
      <div className="intake-body">
        <input
          ref={fileInput}
          id="file-input"
          type="file"
          multiple
          accept=".mp4,.ts,.wav,.mp3,.txt"
          disabled={busy || uncertain}
          onChange={(e) => addFiles(e.target.files)}
          className="file-input"
        />
        <label
          htmlFor="file-input"
          className={"drop-zone" + (busy || uncertain ? " disabled" : "")}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (!busy && !uncertain) addFiles(e.dataTransfer.files);
          }}
        >
          <span className="upload-symbol" aria-hidden="true">
            ↑
          </span>
          <span>
            <strong>파일을 놓거나 선택하세요</strong>
            <small>영상 · 오디오 · UTF-8 텍스트</small>
          </span>
          <span className="file-types">MP4 / TS / WAV / MP3 / TXT</span>
        </label>
        {error && (
          <p role="alert" className="inline-error" style={{ margin: "12px 0 0" }}>
            {error}
          </p>
        )}
        {files.length > 0 && (
          <ul className="file-list">
            {files.map((file, index) => (
              <li key={file.name + index}>
                <span>{file.name}</span>
                <small>
                  {bytes(file.size)} · {stageHint(file.name)}
                  {uploads[index]
                    ? " · " +
                      (uploads[index].status === "ready"
                        ? "업로드 완료"
                        : "업로드 중")
                    : ""}
                </small>
                <button
                  aria-label={file.name + " 제거"}
                  disabled={busy || uncertain}
                  onClick={() =>
                    setFiles((old) => old.filter((_, i) => i !== index))
                  }
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
        <div className="intake-footer">
          <label className="inline-label">
            마지막 처리 단계
            <select
              aria-label="마지막 처리 단계"
              disabled={busy || uncertain}
              value={endStage}
              onChange={(e) => setEndStage(Number(e.target.value))}
            >
              <option value={4}>요약 / 프롬프트 준비</option>
              <option value={3}>음성 인식까지만</option>
              <option value={2}>오디오 변환까지만</option>
              <option value={1}>다운로드까지만 (LMS URL)</option>
            </select>
          </label>
          <button
            className="primary"
            disabled={busy || !files.length || !settings}
            onClick={() => void submit()}
          >
            {busy
              ? "업로드·작업 추가 중…"
              : uncertain
                ? "제출 다시 확인 →"
                : files.length
                  ? `${files.length}개 작업 시작 →`
                  : "작업 시작 →"}
          </button>
        </div>
      </div>
    </section>
  );
}
