import type { Job } from "../types";
import { stages } from "../lib/format";

export function OverviewStats({
  working,
  completed,
}: {
  working: Job[];
  completed: Job[];
}) {
  const runs = working.flatMap((job) => job.attempts.at(-1)?.stages ?? []);
  return (
    <section className="overview" aria-label="작업 현황">
      <div className="stat-card">
        <span className="stat-number">
          {String(working.length).padStart(2, "0")}
        </span>
        <span className="stat-label">처리 중인 작업</span>
      </div>
      <div className="stat-card is-done">
        <span className="stat-number">
          {String(completed.length).padStart(2, "0")}
        </span>
        <span className="stat-label">완료된 작업</span>
      </div>
      <div className="pipeline-summary">
        {stages.map((stage, index) => {
          const rows = runs.filter((run) => run.stage === index + 1);
          return (
            <div className="pipeline-step" key={stage}>
              <span className="step-index">STEP 0{index + 1}</span>
              <strong>{stage}</strong>
              <small>
                대기 {rows.filter((run) => run.status === "queued").length} ·
                실행 {rows.filter((run) => run.status === "running").length}
              </small>
            </div>
          );
        })}
      </div>
    </section>
  );
}
