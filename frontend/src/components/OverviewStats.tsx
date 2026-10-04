import type { Job } from "../types";
import {
  isActive,
  matchesJobFilter,
  stages,
  type JobFilter,
} from "../lib/format";

const filters: { value: JobFilter; label: string }[] = [
  { value: "all", label: "전체" },
  { value: "active", label: "처리 중" },
  { value: "completed", label: "완료" },
  { value: "retryable", label: "확인 필요" },
];

export function OverviewStats({
  jobs,
  filter,
  onFilter,
  incompletePlaybacks,
  onIncomplete,
  isLoading,
}: {
  jobs: Job[];
  filter: JobFilter;
  onFilter: (filter: JobFilter) => void;
  incompletePlaybacks: number;
  onIncomplete: () => void;
  isLoading: boolean;
}) {
  const working = jobs.filter(isActive);
  const runs = working.flatMap((job) => job.attempts.at(-1)?.stages ?? []);
  return (
    <section className="workspace-overview" aria-label="작업 현황">
      <div className="workspace-status-bar">
        <div
          className="status-filters"
          role="group"
          aria-label="작업 상태 필터"
        >
          {filters.map(({ value, label }) => (
            <button
              key={value}
              className={"status-filter" + (filter === value ? " active" : "")}
              aria-pressed={filter === value}
              disabled={isLoading}
              onClick={() => onFilter(value)}
            >
              {label}
              <span>
                {isLoading
                  ? "…"
                  : jobs.filter((job) => matchesJobFilter(job, value)).length}
              </span>
            </button>
          ))}
        </div>
        {incompletePlaybacks > 0 && (
          <button
            className="playback-alert"
            onClick={onIncomplete}
            disabled={isLoading}
          >
            미완료 재생 <strong>{incompletePlaybacks}</strong>
            <span aria-hidden="true"> →</span>
          </button>
        )}
      </div>
      <details className="pipeline-details">
        <summary>
          단계별 처리 현황{" "}
          <span>
            {isLoading
              ? "불러오는 중"
              : working.length
                ? `${working.length}개 작업 처리 중`
                : "처리 중인 작업 없음"}
          </span>
        </summary>
        <div className="pipeline-summary">
          {stages.map((stage, index) => {
            const rows = runs.filter((run) => run.stage === index + 1);
            return (
              <div className="pipeline-step" key={stage}>
                <strong>{stage}</strong>
                <small>
                  대기 {rows.filter((run) => run.status === "queued").length} ·
                  실행 {rows.filter((run) => run.status === "running").length}
                </small>
              </div>
            );
          })}
        </div>
      </details>
    </section>
  );
}
