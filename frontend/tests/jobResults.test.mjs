import { test } from "node:test";
import assert from "node:assert/strict";
import {
  getAvailableArtifacts,
  getSelectedArtifact,
  getStageRuns,
  getResumableStage,
} from "../src/lib/jobResults.ts";

const artifact = (id, kind, attempt_id = "first", state = "complete") => ({
  id,
  kind,
  attempt_id,
  state,
  display_name: kind + ".txt",
});
const stage = (stage, status, output_id = null) => ({
  stage,
  status,
  output_id,
});
const job = (values = {}) => ({
  id: "lecture",
  current_attempt_id: "first",
  status: "running",
  end_stage: 4,
  retryable: false,
  artifacts: [],
  attempts: [],
  ...values,
});

test("new transcript and summary appear while job remains running", () => {
  const running = job();
  assert.equal(getSelectedArtifact(running, null), null);
  running.artifacts = [artifact("transcript", "transcript")];
  assert.equal(getSelectedArtifact(running, null)?.id, "transcript");
  running.artifacts.push(artifact("summary", "summary"));
  assert.equal(getSelectedArtifact(running, null)?.id, "summary");
  assert.equal(running.status, "running");
});

test("streaming summary does not replace a manually selected transcript", () => {
  const running = job({ artifacts: [artifact("transcript", "transcript")] });
  const choice = { jobId: "lecture", attemptId: "first", kind: "transcript" };
  running.artifacts.push(artifact("summary", "summary"));
  assert.equal(getSelectedArtifact(running, choice)?.id, "transcript");
  running.current_attempt_id = "second";
  assert.equal(getSelectedArtifact(running, choice)?.id, "summary");
  assert.equal(getSelectedArtifact(null, choice), null);
});

test("retained results survive resume but current attempt and removed artifacts take precedence", () => {
  const resumed = job({
    current_attempt_id: "second",
    artifacts: [
      artifact("latest-summary", "summary", "second"),
      artifact("old-summary", "summary"),
      artifact("transcript", "transcript"),
      artifact("audio", "audio", "first", "deleted"),
    ],
  });
  assert.deepEqual(
    getAvailableArtifacts(resumed).map(({ id }) => id),
    ["latest-summary", "transcript"],
  );
  resumed.artifacts[0].state = "deleted";
  assert.equal(getSelectedArtifact(resumed, null)?.id, "old-summary");
});

test("list and detail retain earlier completed stages after resume", () => {
  const resumed = job({
    current_attempt_id: "second",
    retryable: true,
    artifacts: [artifact("transcript", "transcript")],
    attempts: [
      {
        id: "first",
        stages: [stage(3, "completed", "transcript"), stage(4, "failed")],
      },
      { id: "second", stages: [stage(4, "running")] },
    ],
  });
  const runs = getStageRuns(resumed);
  assert.equal(runs.get(3)?.status, "completed");
  assert.equal(runs.get(4)?.status, "running");
  assert.equal(getResumableStage(resumed), 4);
  resumed.artifacts[0].state = "deleted";
  assert.equal(getResumableStage(resumed), null);
});

test("a new attempt running a stage overrides its older completion", () => {
  const retried = job({
    retryable: true,
    end_stage: 3,
    artifacts: [artifact("transcript", "transcript")],
    attempts: [
      { stages: [stage(3, "completed", "transcript")] },
      { stages: [stage(3, "failed")] },
    ],
  });
  assert.equal(getStageRuns(retried).get(3)?.status, "failed");
  assert.equal(getResumableStage(retried), null);
});
