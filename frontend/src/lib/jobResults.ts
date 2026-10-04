import type { Artifact, Job, Stage } from "../types";

/** Keep one retained result of each kind, preferring the current attempt. */
export function getAvailableArtifacts(job: Job | null): Artifact[] {
  const byKind = new Map<string, Artifact>();
  for (const item of job?.artifacts ?? []) {
    if (item.state !== "complete") continue;
    const existing = byKind.get(item.kind);
    if (
      !existing ||
      item.attempt_id === job?.current_attempt_id ||
      existing.attempt_id !== job?.current_attempt_id
    )
      byKind.set(item.kind, item);
  }
  return [...byKind.values()];
}

export function getPreferredArtifact(available: Artifact[]): Artifact | null {
  return (
    available.find((item) => item.kind === "summary") ??
    available.find((item) => item.kind === "prompt") ??
    available.find((item) => item.kind === "transcript") ??
    null
  );
}

export type ArtifactSelection = {
  jobId: string;
  attemptId: string;
  kind: string;
};

/** New streamed results are selected automatically until a reader picks a tab. */
export function getSelectedArtifact(
  job: Job | null,
  selection: ArtifactSelection | null,
): Artifact | null {
  const available = getAvailableArtifacts(job);
  if (
    selection?.jobId === job?.id &&
    selection?.attemptId === job?.current_attempt_id
  ) {
    const selected = available.find((item) => item.kind === selection?.kind);
    if (selected) return selected;
  }
  return getPreferredArtifact(available);
}

function getLiveStageRuns(job: Job): Map<number, Stage> {
  const liveArtifacts = new Set(
    job.artifacts
      .filter((item) => item.state === "complete")
      .map((item) => item.id),
  );
  const runs = new Map<number, Stage>();
  for (const attempt of job.attempts) {
    for (const run of attempt.stages) {
      if (
        run.status === "completed" &&
        run.output_id &&
        liveArtifacts.has(run.output_id)
      )
        runs.set(run.stage, run);
    }
  }
  return runs;
}

/** The current attempt wins; retained earlier work fills stages it did not run. */
export function getStageRuns(job: Job): Map<number, Stage> {
  const runs = new Map<number, Stage>();
  for (const attempt of job.attempts) {
    for (const run of attempt.stages) runs.set(run.stage, run);
  }
  for (const [stage, run] of getLiveStageRuns(job)) runs.set(stage, run);
  for (const run of job.attempts.at(-1)?.stages ?? []) runs.set(run.stage, run);
  return runs;
}

export function getResumableStage(job: Job): number | null {
  if (!job.retryable) return null;
  const completedStages = [...getLiveStageRuns(job).keys()];
  if (!completedStages.length) return null;
  const nextStage = Math.max(...completedStages) + 1;
  return nextStage <= job.end_stage ? nextStage : null;
}
