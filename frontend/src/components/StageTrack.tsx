import type { Job } from "../types";
import { stages } from "../lib/format";

export function StageTrack({ job }: { job: Job }) {
  const latest = job.attempts.at(-1);
  return (
    <ol className="stage-track" aria-label="처리 단계">
      {stages.map((label, index) => {
        const run = latest?.stages.find((stage) => stage.stage === index + 1);
        return (
          <li key={label} className={run?.status ?? "skipped"}>
            <span>
              {run?.status === "completed"
                ? "✓"
                : String(index + 1).padStart(2, "0")}
            </span>
            {label}
          </li>
        );
      })}
    </ol>
  );
}
