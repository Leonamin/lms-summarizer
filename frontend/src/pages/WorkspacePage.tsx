import { useJobResult } from "../hooks/useJobResult";
import {
  PlaybackHistory,
  type PlaybackFilter,
} from "../components/PlaybackHistory";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Job, Playback, SettingsResponse } from "../types";
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
  isLoading = false,
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
  isLoading?: boolean;
  onNotice: (message: string) => void;
  onCommand: (
    job: Job,
    action: "cancel" | "retry" | "resume",
    shouldUseCurrentSettings?: boolean,
  ) => void;
  onContinue: (job: Job, endStage: number) => void;
  onStopAll: () => void;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const [filter, setFilter] = useState<JobFilter>("all");
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [revealRequest, setRevealRequest] = useState<{ id: string } | null>(
    null,
  );
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
  const [playbacks, setPlaybacks] = useState<Playback[]>([]);
  const [isPlaybackOpen, setIsPlaybackOpen] = useState(false);
  const [playbackFilter, setPlaybackFilter] = useState<PlaybackFilter>("all");

  // Auto-play runs in the same single slot as jobs; surface it in the list.
  useEffect(() => {
    let isAlive = true;
    const load = () =>
      api<{ records: Playback[] }>("/playback")
        .then((result) => {
          if (isAlive) setPlaybacks(result.records);
        })
        .catch(() => {});
    void load();
    const timer = setInterval(load, 5000);
    return () => {
      isAlive = false;
      clearInterval(timer);
    };
  }, []);

  const current = jobs.find((job) => job.id === selected) ?? null;

  const { available, artifact, text, isLoadingText, jobModel, openArtifact } =
    useJobResult(current, report);

  const onSubmitted = useCallback(
    async (ids: string[]) => {
      const added = await Promise.all(ids.map((id) => api<Job>("/jobs/" + id)));
      merge(added);
      if (ids[0]) {
        setSelected(ids[0]);
        setRevealRequest({ id: ids[0] });
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
    setIsPlaybackOpen(true);
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
            isLoading={isLoading}
          />
        </div>
        <div className="workspace-grid">
          <div className="workspace-list-pane" ref={listRef}>
            <JobList
              jobs={jobs}
              selected={selected}
              onSelect={selectJob}
              onSelectionChange={setSelected}
              filter={filter}
              onFilter={setFilter}
              revealRequest={revealRequest}
              onImport={() => onNavigate("import")}
              isVisible={view === "workspace"}
              hasOpenDetail={isDetailOpen}
              onStopAll={onStopAll}
              isLoading={isLoading}
            >
              <PlaybackHistory
                playbacks={playbacks}
                isOpen={isPlaybackOpen}
                onOpenChange={setIsPlaybackOpen}
                filter={playbackFilter}
                onFilterChange={setPlaybackFilter}
                onRetry={(item) => void retryPlayback(item)}
                onRevealJob={(id) => {
                  if (!jobs.some((job) => job.id === id)) {
                    onNotice("연결된 작업을 찾을 수 없습니다.");
                    return;
                  }
                  setRevealRequest({ id });
                  selectJob(id);
                }}
              />
            </JobList>
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
              isLoading={isLoadingText}
              pending={pending}
              jobModel={jobModel}
              onOpenArtifact={openArtifact}
              onCommand={onCommand}
              onContinue={onContinue}
              onNotice={onNotice}
              isLoadingFallback={isLoading}
            />
          </div>
        </div>
      </div>
    </>
  );
}
