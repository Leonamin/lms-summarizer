import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Artifact, Job, SettingsResponse } from "../types";
import { isActive } from "../lib/format";
import { IntakePanel } from "../components/IntakePanel";
import { JobList } from "../components/JobList";
import { LmsImportPanel } from "../components/LmsImportPanel";
import { OverviewStats } from "../components/OverviewStats";
import { ResultPanel } from "../components/ResultPanel";

export function WorkspacePage({
  jobs,
  settings,
  merge,
  report,
  pending,
  onNotice,
  onCommand,
  onStopAll,
}: {
  jobs: Job[];
  settings: SettingsResponse | null;
  merge: (jobs: Job[]) => void;
  report: (cause: unknown) => void;
  pending: string | null;
  onNotice: (message: string) => void;
  onCommand: (job: Job, action: "cancel" | "retry") => void;
  onStopAll: () => void;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const [endStage, setEndStage] = useState(4);
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [text, setText] = useState("");
  const [loadingText, setLoadingText] = useState(false);
  const [jobModel, setJobModel] = useState("chatgpt");
  const contentRequest = useRef(0);

  // Keep a valid selection as jobs stream in and out.
  useEffect(() => {
    if (jobs.length && !jobs.some((job) => job.id === selected))
      setSelected(jobs[0].id);
  }, [jobs, selected]);

  const current = jobs.find((job) => job.id === selected) ?? null;

  useEffect(() => {
    let alive = true;
    setJobModel("chatgpt");
    if (current)
      api<{ settings: { ai_model: string } }>("/jobs/" + current.id + "/settings")
        .then((result) => {
          if (alive) setJobModel(result.settings.ai_model);
        })
        .catch(() => {});
    return () => {
      alive = false;
    };
  }, [current?.id, current?.settings_revision_id]);

  const openArtifact = useCallback(
    async (item: Artifact) => {
      const sequence = ++contentRequest.current;
      setArtifact(item);
      setText("");
      setLoadingText(true);
      try {
        const result = await api<{ text: string }>(
          "/artifacts/" + item.id + "/content",
        );
        if (sequence === contentRequest.current) setText(result.text);
      } catch (cause) {
        if (sequence === contentRequest.current) report(cause);
      } finally {
        if (sequence === contentRequest.current) setLoadingText(false);
      }
    },
    [report],
  );

  useEffect(() => {
    contentRequest.current++;
    setArtifact(null);
    setText("");
    setLoadingText(false);
    const latest = current?.artifacts.filter(
      (item) =>
        item.state === "complete" &&
        item.attempt_id === current.current_attempt_id,
    );
    const preferred =
      latest?.find((item) => item.kind === "summary") ??
      latest?.find((item) => item.kind === "prompt") ??
      latest?.find((item) => item.kind === "transcript");
    if (preferred) void openArtifact(preferred);
  }, [current?.id, current?.current_attempt_id, current?.status, openArtifact]);

  const onSubmitted = useCallback(
    async (ids: string[]) => {
      const added = await Promise.all(
        ids.map((id) => api<Job>("/jobs/" + id)),
      );
      merge(added);
      if (ids[0]) setSelected(ids[0]);
      onNotice(
        `${added.length}개 작업을 추가했습니다. 이 화면을 닫아도 처리는 계속됩니다.`,
      );
    },
    [merge, onNotice],
  );

  const available =
    current?.artifacts.filter(
      (item) =>
        item.state === "complete" &&
        (item.attempt_id === current.current_attempt_id ||
          item.attempt_id === null),
    ) ?? [];

  return (
    <>
      <OverviewStats
        working={jobs.filter(isActive)}
        completed={jobs.filter((job) => job.status === "completed")}
      />
      <LmsImportPanel
        settings={settings}
        endStage={endStage}
        setEndStage={setEndStage}
        onSubmitted={onSubmitted}
        report={report}
      />
      <IntakePanel
        settings={settings}
        endStage={endStage}
        setEndStage={setEndStage}
        onSubmitted={onSubmitted}
        report={report}
      />
      <div className="workspace-grid">
        <JobList
          jobs={jobs}
          selected={selected}
          onSelect={setSelected}
          onStopAll={onStopAll}
        />
        <ResultPanel
          job={current}
          available={available}
          artifact={artifact}
          text={text}
          loading={loadingText}
          pending={pending}
          jobModel={jobModel}
          onOpenArtifact={(item) => void openArtifact(item)}
          onCommand={onCommand}
          onNotice={onNotice}
        />
      </div>
    </>
  );
}
