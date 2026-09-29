import type { Job, Stage } from "../types";
import { stages } from "../lib/format";
import { stageIcons, stageRunLabels } from "../lib/stageIcons";

export function StageTrack({ job }: { job: Job }) {
  const liveArtifacts = new Set(
    job.artifacts
      .filter((item) => item.state === "complete")
      .map((item) => item.id),
  );
  // Merge stages across attempts so earlier completed work stays visible after
  // a resume/retry. The latest attempt wins for stages it actually ran; stages
  // it skipped fall back to the newest run that produced a live artifact.
  const latestRuns = new Map<number, Stage>();
  const liveRuns = new Map<number, Stage>();
  const anyRuns = new Map<number, Stage>();
  for (const attempt of job.attempts) {
    for (const run of attempt.stages) {
      anyRuns.set(run.stage, run);
      if (
        run.status === "completed" &&
        run.output_id &&
        liveArtifacts.has(run.output_id)
      ) {
        liveRuns.set(run.stage, run);
      }
    }
  }
  for (const run of job.attempts.at(-1)?.stages ?? []) {
    latestRuns.set(run.stage, run);
  }
  return (
    <ol className="stage-track" aria-label="처리 단계">
      {stages.map((label, index) => {
        const stage = index + 1;
        const run =
          latestRuns.get(stage) ?? liveRuns.get(stage) ?? anyRuns.get(stage);
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
