import type { Artifact, Job } from "../types";
import {
  chatbotUrls,
  formatDate,
  isActive,
  kindLabels,
  statusLabels,
} from "../lib/format";
import { ArtifactReader } from "./ArtifactReader";
import { JobLogs } from "./JobLogs";
import { StageTrack } from "./StageTrack";
import { StatusBadge } from "./StatusBadge";

export function ResultPanel({
  job,
  available,
  artifact,
  text,
  loading,
  pending,
  jobModel,
  onOpenArtifact,
  onCommand,
  onNotice,
  loadingFallback = false,
}: {
  job: Job | null;
  available: Artifact[];
  artifact: Artifact | null;
  text: string;
  loading: boolean;
  pending: string | null;
  jobModel: string;
  onOpenArtifact: (artifact: Artifact) => void;
  onCommand: (job: Job, action: "cancel" | "retry") => void;
  onNotice: (message: string) => void;
  loadingFallback?: boolean;
}) {
  if (!job) {
    return (
      <section className="result-panel panel" aria-label="작업 상세">
        {loadingFallback ? (
          <div className="result-skeleton" aria-hidden="true">
            <div className="skeleton sk-title" />
            <div className="skeleton sk-track" />
            <div className="skeleton sk-line" />
            <div className="skeleton sk-line" />
            <div className="skeleton sk-line short" />
            <div className="skeleton sk-block" />
          </div>
        ) : (
          <div className="empty result-empty">
            <span aria-hidden="true">↗</span>
            <h3>결과를 읽는 공간</h3>
            <p>
              작업을 선택하면 처리 단계와
              <br />
              원문·요약을 함께 확인할 수 있습니다.
            </p>
          </div>
        )}
      </section>
    );
  }

  const latest = job.attempts.at(-1);
  return (
    <section className="result-panel panel" aria-label="작업 상세">
      <div className="section-heading">
        <div>
          <span className="eyebrow">WORK &amp; RESULTS</span>
          <h2>{job.display_name}</h2>
        </div>
        <StatusBadge job={job} />
      </div>
      <StageTrack job={job} />
      <div className="detail-actions">
        <small>
          시도 {job.attempts.length}회 · {formatDate(job.created_at)}
        </small>
        <div>
          {["queued", "running", "cancelling"].includes(job.status) && (
            <button
              disabled={pending === job.id}
              className="button-danger"
              onClick={() => onCommand(job, "cancel")}
            >
              작업 취소
            </button>
          )}
          {job.retryable && (
            <button
              disabled={pending === job.id}
              className="secondary"
              onClick={() => onCommand(job, "retry")}
            >
              다시 시도
            </button>
          )}
        </div>
      </div>
      {latest?.safe_message && (
        <p className="inline-error">{latest.safe_message}</p>
      )}
      {job.result_kind === "manual_ready" && (
        <p className="manual-note" style={{ margin: "0 24px 14px" }}>
          프롬프트가 준비되었습니다. 복사한 뒤{" "}
          <a
            href={chatbotUrls[jobModel] ?? chatbotUrls.chatgpt}
            target="_blank"
            rel="noreferrer"
          >
            챗봇 열기 ↗
          </a>
          에서 붙여넣으세요.
        </p>
      )}
      {available.length > 0 ? (
        <>
          <div
            className="artifact-tabs"
            role="group"
            aria-label="결과 파일"
          >
            {available.map((item) => (
              <button
                key={item.id}
                className={artifact?.id === item.id ? "active" : ""}
                onClick={() => onOpenArtifact(item)}
                disabled={!item.display_name.endsWith(".txt")}
              >
                {kindLabels[item.kind] ?? item.kind}
              </button>
            ))}
          </div>
          {artifact && (
            <div className="file-downloads">
              {available
                .filter((item) => !item.display_name.endsWith(".txt"))
                .map((item) => (
                  <a
                    key={item.id}
                    href={"/api/v1/artifacts/" + item.id + "/download"}
                    download
                  >
                    {kindLabels[item.kind] ?? item.kind} 다운로드 ↓
                  </a>
                ))}
            </div>
          )}
          {artifact && (
            <ArtifactReader
              artifact={artifact}
              text={text}
              loading={loading}
              onNotice={onNotice}
            />
          )}
          {!artifact && (
            <div className="file-downloads">
              {available.map((item) => (
                <a
                  key={item.id}
                  href={"/api/v1/artifacts/" + item.id + "/download"}
                  download
                >
                  {kindLabels[item.kind] ?? item.kind} 다운로드 ↓
                </a>
              ))}
            </div>
          )}
        </>
      ) : (
        <div className="empty result-empty">
          <span aria-hidden="true">↗</span>
          <h3>
            {isActive(job)
              ? "차근차근 처리하고 있습니다."
              : "이 작업에는 아직 결과가 없습니다."}
          </h3>
          <p>
            {isActive(job)
              ? "결과가 준비되면 이곳에 표시됩니다."
              : "실패·취소·중단된 작업은 다시 시도할 수 있습니다."}
          </p>
        </div>
      )}
      <JobLogs job={job} />
      <details className="attempt-history">
        <summary>시도 이력</summary>
        {job.attempts.map((attempt) => (
          <p key={attempt.id}>
            시도 {attempt.number} · {statusLabels[attempt.status]}{" "}
            {attempt.safe_message ? "· " + attempt.safe_message : ""}
          </p>
        ))}
      </details>
    </section>
  );
}
