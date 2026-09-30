import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Artifact, Job, Playback, SettingsResponse } from "../types";
import { isActive, isPlaybackActive, isPlaybackIncomplete } from "../lib/format";
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
  loading = false,
  onNotice,
  onCommand,
  onContinue,
  onStopAll,
}: {
  jobs: Job[];
  settings: SettingsResponse | null;
  merge: (jobs: Job[]) => void;
  report: (cause: unknown) => void;
  pending: string | null;
  loading?: boolean;
  onNotice: (message: string) => void;
  onCommand: (job: Job, action: "cancel" | "retry" | "resume", useCurrentSettings?: boolean) => void;
  onContinue: (job: Job, endStage: number) => void;
  onStopAll: () => void;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const [endStage, setEndStage] = useState(4);
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [text, setText] = useState("");
  const [loadingText, setLoadingText] = useState(false);
  const [jobModel, setJobModel] = useState("chatgpt");
  const [playbacks, setPlaybacks] = useState<Playback[]>([]);
  const [playbackOpen, setPlaybackOpen] = useState(false);
  const [playbackFilter, setPlaybackFilter] = useState<
    "all" | "unattended" | "incomplete"
  >("all");
  const contentRequest = useRef(0);

  // Auto-play runs in the same single slot as jobs; surface it in the list.
  useEffect(() => {
    let alive = true;
    const load = () =>
      api<{ records: Playback[] }>("/playback")
        .then((result) => {
          if (alive) setPlaybacks(result.records);
        })
        .catch(() => {});
    void load();
    const timer = setInterval(load, 5000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

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

  // Keep one live artifact per kind across every attempt, preferring the
  // current attempt, so resuming/extending never hides earlier results.
  const available: Artifact[] = (() => {
    if (!current) return [];
    const currentId = current.current_attempt_id;
    const byKind = new Map<string, Artifact>();
    for (const item of current.artifacts) {
      if (item.state !== "complete") continue;
      const existing = byKind.get(item.kind);
      if (!existing) {
        byKind.set(item.kind, item);
        continue;
      }
      const itemPreferred = item.attempt_id === currentId;
      const existingPreferred = existing.attempt_id === currentId;
      if (itemPreferred || !existingPreferred) byKind.set(item.kind, item);
    }
    return [...byKind.values()];
  })();

  useEffect(() => {
    contentRequest.current++;
    setArtifact(null);
    setText("");
    setLoadingText(false);
    const preferred =
      available.find((item) => item.kind === "summary") ??
      available.find((item) => item.kind === "prompt") ??
      available.find((item) => item.kind === "transcript");
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

  const incompletePlaybacks = playbacks.filter((item) =>
    isPlaybackIncomplete(item.status),
  ).length;

  const showIncompletePlaybacks = useCallback(() => {
    setPlaybackFilter("incomplete");
    setPlaybackOpen(true);
    requestAnimationFrame(() =>
      document
        .getElementById("playback-group")
        ?.scrollIntoView({ block: "start", behavior: "smooth" }),
    );
  }, []);

  return (
    <>
      <OverviewStats
        working={jobs.filter(isActive)}
        completed={jobs.filter((job) => job.status === "completed")}
        incompletePlaybacks={incompletePlaybacks}
        incompleteActive={playbackFilter === "incomplete"}
        onIncomplete={showIncompletePlaybacks}
        loading={loading}
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
          playbacks={playbacks}
          selected={selected}
          onSelect={setSelected}
          onStopAll={onStopAll}
          loading={loading}
          playbackOpen={playbackOpen}
          setPlaybackOpen={setPlaybackOpen}
          playbackFilter={playbackFilter}
          setPlaybackFilter={setPlaybackFilter}
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
          onContinue={onContinue}
          onNotice={onNotice}
          loadingFallback={loading}
        />
      </div>
    </>
  );
}
