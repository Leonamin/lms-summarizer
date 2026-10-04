import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Artifact, Job, Playback, SettingsResponse } from "../types";
import { isPlaybackIncomplete, type JobFilter, type View } from "../lib/format";
import { ImportPage } from "./ImportPage";
import { JobList } from "../components/JobList";
import { OverviewStats } from "../components/OverviewStats";
import { ResultPanel } from "../components/ResultPanel";

export function WorkspacePage({
  view,
  onNavigate,
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
  view: View;
  onNavigate: (view: View) => void;
  jobs: Job[];
  settings: SettingsResponse | null;
  merge: (jobs: Job[]) => void;
  report: (cause: unknown) => void;
  pending: string | null;
  loading?: boolean;
  onNotice: (message: string) => void;
  onCommand: (
    job: Job,
    action: "cancel" | "retry" | "resume",
    useCurrentSettings?: boolean,
  ) => void;
  onContinue: (job: Job, endStage: number) => void;
  onStopAll: () => void;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const [filter, setFilter] = useState<JobFilter>("all");
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [revealJobId, setRevealJobId] = useState<string | null>(null);
  const listScroll = useRef(0);
  const hasDetailHistory = useRef(false);
  const detailRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const selectedRef = useRef(selected);
  selectedRef.current = selected;

  useEffect(() => {
    const syncDetail = () => {
      const id = window.location.hash.match(/^#workspace\/([^/]+)$/)?.[1];
      setIsDetailOpen(!!id);
      if (id) setSelected(id);
      if (!window.matchMedia("(max-width: 1180px)").matches) return;
      const route = window.location.hash.slice(1).split("/")[0];
      if (route && route !== "workspace") return;
      requestAnimationFrame(() => {
        if (id) {
          detailRef.current?.focus({ preventScroll: true });
          detailRef.current?.scrollIntoView({ block: "start" });
        } else {
          const row = Array.from(
            listRef.current?.querySelectorAll<HTMLButtonElement>(".job-row") ??
              [],
          ).find((item) => item.dataset.jobId === selectedRef.current);
          row?.focus({ preventScroll: true });
          window.scrollTo({ top: listScroll.current, behavior: "instant" });
        }
      });
    };
    syncDetail();
    window.addEventListener("hashchange", syncDetail);
    return () => window.removeEventListener("hashchange", syncDetail);
  }, []);

  const selectJob = (id: string) => {
    setSelected(id);
    if (window.matchMedia("(max-width: 1180px)").matches) {
      listScroll.current = window.scrollY;
      hasDetailHistory.current = true;
      window.location.hash = `workspace/${id}`;
    }
  };
  const backToList = () => {
    if (hasDetailHistory.current) {
      hasDetailHistory.current = false;
      window.history.back();
    } else window.location.hash = "workspace";
  };
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

  const current = jobs.find((job) => job.id === selected) ?? null;

  useEffect(() => {
    let alive = true;
    setJobModel("chatgpt");
    if (current)
      api<{ settings: { ai_model: string } }>(
        "/jobs/" + current.id + "/settings",
      )
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
      const added = await Promise.all(ids.map((id) => api<Job>("/jobs/" + id)));
      merge(added);
      if (ids[0]) {
        setSelected(ids[0]);
        setRevealJobId(ids[0]);
      }
      onNavigate("workspace");
      onNotice(
        `${added.length}개 작업을 추가했습니다. 이 화면을 닫아도 처리는 계속됩니다.`,
      );
    },
    [merge, onNotice, onNavigate],
  );

  const incompletePlaybacks = playbacks.filter((item) =>
    isPlaybackIncomplete(item.status),
  ).length;

  const showIncompletePlaybacks = useCallback(() => {
    setIsDetailOpen(false);
    hasDetailHistory.current = false;
    window.history.replaceState(null, "", "#workspace");
    setPlaybackFilter("incomplete");
    setPlaybackOpen(true);
    requestAnimationFrame(() => {
      const group = document.getElementById("playback-group");
      group?.scrollIntoView({ block: "start", behavior: "instant" });
      group?.focus({ preventScroll: true });
    });
  }, []);

  const retryPlayback = async (item: Playback) => {
    try {
      await api(`/playback/${item.id}/retry`, { method: "POST", body: "{}" });
      const result = await api<{ records: Playback[] }>("/playback");
      setPlaybacks(result.records);
      onNotice("재생을 다시 큐에 넣었습니다.");
    } catch (cause) {
      report(cause);
    }
  };

  return (
    <>
      <div hidden={view !== "import"}>
        <ImportPage
          settings={settings}
          onSubmitted={onSubmitted}
          report={report}
          onSettings={() => onNavigate("settings")}
        />
      </div>
      <div
        hidden={view !== "workspace"}
        className={isDetailOpen ? "workspace has-detail" : "workspace"}
      >
        <div className="workspace-list-overview">
          <OverviewStats
            jobs={jobs}
            filter={filter}
            onFilter={setFilter}
            incompletePlaybacks={incompletePlaybacks}
            onIncomplete={showIncompletePlaybacks}
            isLoading={loading}
          />
        </div>
        <div className="workspace-grid">
          <div className="workspace-list-pane" ref={listRef}>
            <JobList
              jobs={jobs}
              playbacks={playbacks}
              selected={selected}
              onSelect={selectJob}
              onSelectionChange={setSelected}
              filter={filter}
              onFilter={setFilter}
              revealJobId={revealJobId}
              onImport={() => onNavigate("import")}
              isVisible={view === "workspace"}
              hasOpenDetail={isDetailOpen}
              onStopAll={onStopAll}
              loading={loading}
              playbackOpen={playbackOpen}
              setPlaybackOpen={setPlaybackOpen}
              playbackFilter={playbackFilter}
              setPlaybackFilter={setPlaybackFilter}
              onPlaybackRetry={(item) => void retryPlayback(item)}
            />
          </div>
          <div
            id="job-result"
            className="workspace-detail-pane"
            ref={detailRef}
            tabIndex={-1}
            aria-label="선택한 작업 상세"
          >
            <button className="ghost back-to-list" onClick={backToList}>
              ← 작업 목록으로
            </button>
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
        </div>
      </div>
    </>
  );
}
