import { getResumableStage } from "../lib/jobResults";
import { useEffect, useState } from "react";
import type { Artifact, Job } from "../types";
import {
  chatbotUrls,
  formatDate,
  isActive,
  kindLabels,
  statusLabels,
} from "../lib/format";
import { ArtifactReader } from "./ArtifactReader";
import { Dropdown } from "./Dropdown";
import { JobLogs } from "./JobLogs";
import { StageTrack } from "./StageTrack";
import { StatusBadge } from "./StatusBadge";

export function ResultPanel({
  job,
  available,
  artifact,
  text,
  isLoading,
  pending,
  jobModel,
  onOpenArtifact,
  onCommand,
  onContinue,
  onNotice,
  isLoadingFallback = false,
}: {
  job: Job | null;
  available: Artifact[];
  artifact: Artifact | null;
  text: string;
  isLoading: boolean;
  pending: string | null;
  jobModel: string;
  onOpenArtifact: (artifact: Artifact) => void;
  onCommand: (
    job: Job,
    action: "cancel" | "retry" | "resume",
    shouldUseCurrentSettings?: boolean,
  ) => void;
  onContinue: (job: Job, endStage: number) => void;
  onNotice: (message: string) => void;
  isLoadingFallback?: boolean;
}) {
  const [continueStage, setContinueStage] = useState<number | null>(null);
  const [shouldUseCurrentSettings, setShouldUseCurrentSettings] =
    useState(false);
  useEffect(() => {
    setContinueStage(null);
    setShouldUseCurrentSettings(false);
  }, [job?.id]);
  if (!job) {
    return (
      <section className="result-panel panel" aria-label="작업 상세">
        {isLoadingFallback ? (
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
  const resumableStage = getResumableStage(job);
  const downloads = available.filter(
    (item) => !artifact || !item.display_name.endsWith(".txt"),
  );
  return (
    <section className="result-panel panel" aria-label="작업 상세">
      <div className="section-heading">
        <div>
          <h2>{job.display_name}</h2>
          {(job.course_name || job.week_title) && (
            <p
              className="result-subtitle"
              title={[job.course_name, job.week_title]
                .filter(Boolean)
                .join(" · ")}
            >
              {[job.course_name, job.week_title].filter(Boolean).join(" · ")}
            </p>
          )}
        </div>
        <StatusBadge job={job} />
      </div>
      <details
        className="processing-details"
        key={job.id + job.status}
        open={job.status !== "completed"}
      >
        <summary>처리 단계 · 시도 {job.attempts.length}회</summary>
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
              <>
                <label
                  className="check compact"
                  title="지금 저장된 설정(엔진·모델·프롬프트·키)으로 실행합니다. 끄면 제출 당시 설정을 유지합니다."
                >
                  <input
                    type="checkbox"
                    checked={shouldUseCurrentSettings}
                    onChange={(event) =>
                      setShouldUseCurrentSettings(event.target.checked)
                    }
                  />
                  현재 설정 사용
                </label>
                {resumableStage !== null && (
                  <button
                    disabled={pending === job.id}
                    className="secondary"
                    title={`${resumableStage}단계부터 이어서 처리합니다. 이전 단계 결과를 재사용합니다.${shouldUseCurrentSettings ? " 현재 설정으로 실행합니다." : ""}`}
                    onClick={() =>
                      onCommand(job, "resume", shouldUseCurrentSettings)
                    }
                  >
                    이어서 재개
                  </button>
                )}
                <button
                  disabled={pending === job.id}
                  className={resumableStage !== null ? "quiet" : "secondary"}
                  title={`${job.initial_stage}단계부터 처음부터 다시 시도합니다.${shouldUseCurrentSettings ? " 현재 설정으로 실행합니다." : ""}`}
                  onClick={() =>
                    onCommand(job, "retry", shouldUseCurrentSettings)
                  }
                >
                  {resumableStage !== null ? "처음부터" : "다시 시도"}
                </button>
              </>
            )}
          </div>
        </div>
      </details>
      {job.status === "completed" && job.end_stage < 4 && (
        <div className="continue-row">
          <span className="muted">이어서 처리</span>
          <Dropdown
            value={String(continueStage ?? Math.min(job.end_stage + 1, 4))}
            onChange={(value) => setContinueStage(Number(value))}
            ariaLabel="이어서 처리할 단계"
            options={[
              { value: "2", label: "오디오 변환까지" },
              { value: "3", label: "음성 인식까지" },
              { value: "4", label: "요약까지" },
            ].filter((option) => Number(option.value) > job.end_stage)}
          />
          <button
            className="secondary"
            disabled={pending === job.id}
            onClick={() =>
              onContinue(job, continueStage ?? Math.min(job.end_stage + 1, 4))
            }
          >
            이어서 처리
          </button>
        </div>
      )}
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
          <div className="artifact-tabs" role="group" aria-label="결과 파일">
            {available.map((item) => (
              <button
                key={item.id}
                className={artifact?.id === item.id ? "active" : ""}
                aria-pressed={artifact?.id === item.id}
                onClick={() => onOpenArtifact(item)}
                disabled={!item.display_name.endsWith(".txt")}
              >
                {kindLabels[item.kind] ?? item.kind}
              </button>
            ))}
          </div>
          {downloads.length > 0 && (
            <div className="file-downloads">
              {downloads.map((item) => (
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
              loading={isLoading}
              onNotice={onNotice}
            />
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
