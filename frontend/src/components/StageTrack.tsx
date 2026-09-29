import type { Job } from "../types";
import { stages } from "../lib/format";
import { stageIcons, stageRunLabels } from "../lib/stageIcons";

export function StageTrack({ job }: { job: Job }) {
  const latest = job.attempts.at(-1);
  return (
    <ol className="stage-track" aria-label="처리 단계">
      {stages.map((label, index) => {
        const run = latest?.stages.find((stage) => stage.stage === index + 1);
        const Icon = stageIcons[index];
        return (
          <li key={label} className={run?.status ?? "skipped"}>
            <span title={run ? stageRunLabels[run.status] ?? run.status : "대기"}>
              <Icon size={16} strokeWidth={1.9} aria-hidden="true" />
            </span>
            {label}
          </li>
        );
      })}
    </ol>
  );
}
