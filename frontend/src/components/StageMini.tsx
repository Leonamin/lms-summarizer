import type { Job } from "../types";
import { stages } from "../lib/format";
import { getStageRuns } from "../lib/jobResults";
import { stageIcons, stageRunLabels, stageSlotClass } from "../lib/stageIcons";

const stageRunText = (status?: string) =>
  status ? (stageRunLabels[status] ?? status) : "대기";

/** Compact 4-step pipeline: icon per stage, coloured by that stage's status. */
export function StageMini({ job }: { job: Job }) {
  const latest = job.attempts.at(-1);
  const current = Math.min(
    Math.max(latest?.current_stage ?? job.initial_stage, 1),
    stages.length,
  );
  const runs = getStageRuns(job);
  return (
    <span className="stage-mini">
      {stages.map((label, index) => {
        const number = index + 1;
        const run = runs.get(number);
        const Icon = stageIcons[index];
        return (
          <span
            key={label}
            className={
              "stage-mini-slot " +
              stageSlotClass(run?.status) +
              (number === current ? " current" : "")
            }
            title={`${number}. ${label} · ${stageRunText(run?.status)}`}
          >
            <Icon size={14} strokeWidth={2} aria-hidden="true" />
          </span>
        );
      })}
    </span>
  );
}
