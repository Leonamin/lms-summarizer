import type { Playback } from "../types";
import {
  formatDate,
  isPlaybackActive,
  isPlaybackIncomplete,
  playbackStatusLabels,
} from "../lib/format";
export type PlaybackFilter = "all" | "unattended" | "incomplete";
const playbackFilterOptions = [
  { value: "all", label: "전체" },
  { value: "unattended", label: "미출석" },
  { value: "incomplete", label: "중단·실패" },
] as const;

export function PlaybackHistory({
  playbacks,
  isOpen,
  onOpenChange,
  filter,
  onFilterChange,
  onRetry,
  onRevealJob,
}: {
  playbacks: Playback[];
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  filter: PlaybackFilter;
  onFilterChange: (filter: PlaybackFilter) => void;
  onRetry: (item: Playback) => void;
  onRevealJob: (id: string) => void;
}) {
  const activePlaybacks = playbacks.filter((item) =>
    isPlaybackActive(item.status),
  );
  const playbackHistory = playbacks
    .filter((item) => !isPlaybackActive(item.status))
    .sort((a, b) => b.created_at.localeCompare(a.created_at));
  const playbackFiltered = playbackHistory.filter((item) =>
    filter === "unattended"
      ? !item.attended
      : filter === "incomplete"
        ? isPlaybackIncomplete(item.status)
        : true,
  );
  const visibleHistory = playbackFiltered.slice(0, 20);

  return (
    <>
      {playbacks.length > 0 && (
        <section
          className="playback-group"
          id="playback-group"
          tabIndex={-1}
          aria-label="자동 감지 재생"
        >
          <div className="playback-group-head">
            <strong>자동 감지 재생</strong>
            {playbackHistory.length > 0 && (
              <button
                type="button"
                className="playback-toggle"
                aria-expanded={isOpen}
                onClick={() => onOpenChange(!isOpen)}
              >
                지난 재생 {playbackHistory.length}건
                <span aria-hidden="true">{isOpen ? "▴" : "▾"}</span>
              </button>
            )}
          </div>
          {isOpen && playbackHistory.length > 0 && (
            <div className="playback-filters">
              <div
                className="job-sortby"
                role="group"
                aria-label="재생 이력 필터"
              >
                {playbackFilterOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    className={
                      "segment" + (filter === option.value ? " active" : "")
                    }
                    aria-pressed={filter === option.value}
                    onClick={() => onFilterChange(option.value)}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
              <span className="playback-count">
                {playbackFiltered.length}건
              </span>
            </div>
          )}
          {activePlaybacks.map((item) => (
            <div className="playback-row" key={item.id}>
              <span className={"status " + item.status}>
                {playbackStatusLabels[item.status] ?? item.status}
              </span>
              <span className="job-name" title={item.title || item.lecture_url}>
                {item.title || item.lecture_url}
              </span>
              <span className="playback-time">
                {formatDate(item.created_at)}
              </span>
            </div>
          ))}
          {isOpen &&
            visibleHistory.map((item) => (
              <div className="playback-row playback-history" key={item.id}>
                <span className={"status " + item.status}>
                  {playbackStatusLabels[item.status] ?? item.status}
                </span>
                <span
                  className="job-name"
                  title={item.title || item.lecture_url}
                >
                  {item.title || item.lecture_url}
                </span>
                <span
                  className={
                    "playback-attend " + (item.attended ? "yes" : "no")
                  }
                >
                  {item.attended ? "출석" : "미출석"}
                </span>
                {(item.status === "failed" ||
                  item.status === "interrupted") && (
                  <button
                    type="button"
                    className="playback-link"
                    onClick={() => onRetry(item)}
                    title="이 재생을 다시 큐에 넣습니다."
                  >
                    다시 재생
                  </button>
                )}
                {item.job_ids && item.job_ids.length > 0 && (
                  <button
                    type="button"
                    className="playback-link"
                    onClick={() => onRevealJob(item.job_ids![0])}
                    title={`연결된 작업 ${item.job_ids.length}건 · 클릭하면 해당 작업으로 이동`}
                  >
                    작업 {item.job_ids.length}
                  </button>
                )}
                <span className="playback-time">
                  {formatDate(item.created_at)}
                </span>
              </div>
            ))}
        </section>
      )}
    </>
  );
}
