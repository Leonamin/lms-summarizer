import type { Job } from "../types";
import { getStageRuns } from "../lib/jobResults";
import { stages } from "../lib/format";
import { stageIcons, stageRunLabels } from "../lib/stageIcons";

export function StageTrack({ job }: { job: Job }) {
  const runs = getStageRuns(job);
  return (
    <ol className="stage-track" aria-label="처리 단계">
      {stages.map((label, index) => {
        const stage = index + 1;
        const run = runs.get(stage);
        const Icon = stageIcons[index];
        return (
          <li key={label} className={run?.status ?? "skipped"}>
            <span
              title={run ? (stageRunLabels[run.status] ?? run.status) : "대기"}
            >
              <Icon size={16} strokeWidth={1.9} aria-hidden="true" />
            </span>
            {label}
          </li>
        );
      })}
    </ol>
  );
}
