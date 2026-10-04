import { useEffect, useRef, useState } from "react";
import type { Job, Playback } from "../types";
import {
  formatDate,
  matchesJobFilter,
  type JobFilter,
  isActive,
  isPlaybackActive,
  isPlaybackIncomplete,
  playbackStatusLabels,
  stages,
  statusText,
} from "../lib/format";
import { stageIcons, stageRunLabels, stageSlotClass } from "../lib/stageIcons";

const sortOptions = [
  { value: "desc", label: "최신순" },
  { value: "asc", label: "과거순" },
];

const playbackFilterOptions = [
  { value: "all", label: "전체" },
  { value: "unattended", label: "미출석" },
  { value: "incomplete", label: "중단·실패" },
] as const;

const pageSizes = [10, 20];

type SortKey = "status" | "name" | "attempts" | "created";

type PlaybackFilter = "all" | "unattended" | "incomplete";

const columns: { key: SortKey | null; label: string }[] = [
  { key: "status", label: "상태" },
  { key: "name", label: "이름" },
  { key: null, label: "단계" },
  { key: "attempts", label: "시도" },
  { key: "created", label: "만든 시각" },
];

const compare = (a: Job, b: Job, key: SortKey) => {
  switch (key) {
    case "name":
      return a.display_name.localeCompare(b.display_name);
    case "status":
      return a.status.localeCompare(b.status);
    case "attempts":
      return a.attempts.length - b.attempts.length;
    default:
      return a.created_at.localeCompare(b.created_at);
  }
};

const stageRunText = (status?: string) =>
  status ? (stageRunLabels[status] ?? status) : "대기";

/** Compact 4-step pipeline: icon per stage, coloured by that stage's status. */
function StageMini({ job }: { job: Job }) {
  const latest = job.attempts.at(-1);
  const current = Math.min(
    Math.max(latest?.current_stage ?? job.initial_stage, 1),
    stages.length,
  );
  return (
    <span className="stage-mini">
      {stages.map((label, index) => {
        const number = index + 1;
        const run = latest?.stages.find((stage) => stage.stage === number);
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

export function JobList({
  jobs,
  filter,
  onFilter,
  revealJobId,
  onImport,
  isVisible,
  hasOpenDetail,
  playbacks = [],
  selected,
  onSelect,
  onSelectionChange,
  onStopAll,
  loading = false,
  playbackOpen = false,
  setPlaybackOpen,
  playbackFilter = "all",
  setPlaybackFilter,
  onPlaybackRetry,
}: {
  jobs: Job[];
  filter: JobFilter;
  onFilter: (filter: JobFilter) => void;
  revealJobId: string | null;
  onImport: () => void;
  isVisible: boolean;
  hasOpenDetail: boolean;
  playbacks?: Playback[];
  selected: string | null;
  onSelect: (id: string) => void;
  onSelectionChange: (id: string | null) => void;
  onStopAll: () => void;
  loading?: boolean;
  playbackOpen?: boolean;
  setPlaybackOpen?: (open: boolean) => void;
  playbackFilter?: PlaybackFilter;
  setPlaybackFilter?: (filter: PlaybackFilter) => void;
  onPlaybackRetry?: (item: Playback) => void;
}) {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<{ key: SortKey; dir: "asc" | "desc" }>({
    key: "created",
    dir: "desc",
  });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const revealRef = useRef<string | null>(null);
  const working = jobs.filter(isActive);
  const filtered = jobs.filter(
    (job) =>
      matchesJobFilter(job, filter) &&
      [job.display_name, job.course_name, job.week_title]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  const sorted = [...filtered].sort(
    (a, b) => compare(a, b, sort.key) * (sort.dir === "asc" ? 1 : -1),
  );

  // Return to the first page whenever the result set or its order changes.
  useEffect(() => {
    if (!revealRef.current) setPage(1);
  }, [filter, search, sort.key, sort.dir, pageSize]);

  const pageCount = Math.max(1, Math.ceil(sorted.length / pageSize));
  const currentPage = Math.min(page, pageCount);
  const start = (currentPage - 1) * pageSize;
  const visible = sorted.slice(start, start + pageSize);
  const goTo = (next: number) =>
    setPage(Math.min(Math.max(next, 1), pageCount));
  const rangeStart = sorted.length === 0 ? 0 : start + 1;
  const rangeEnd = Math.min(start + pageSize, sorted.length);

  const activePlaybacks = playbacks.filter((item) =>
    isPlaybackActive(item.status),
  );
  const playbackHistory = playbacks
    .filter((item) => !isPlaybackActive(item.status))
    .sort((a, b) => b.created_at.localeCompare(a.created_at));
  const playbackFiltered = playbackHistory.filter((item) =>
    playbackFilter === "unattended"
      ? !item.attended
      : playbackFilter === "incomplete"
        ? isPlaybackIncomplete(item.status)
        : true,
  );
  const visibleHistory = playbackFiltered.slice(0, 20);

  // Bring a job linked from the auto-play history into view and select it.
  const revealJob = (id: string) => {
    revealRef.current = id;
    onFilter("all");
    setSearch("");
    const ordered = [...jobs].sort(
      (a, b) => compare(a, b, sort.key) * (sort.dir === "asc" ? 1 : -1),
    );
    const index = ordered.findIndex((job) => job.id === id);
    if (index >= 0) setPage(Math.floor(index / pageSize) + 1);
    onSelect(id);
  };

  useEffect(() => {
    if (!revealJobId) return;
    revealRef.current = revealJobId;
    onFilter("all");
    setSearch("");
    const ordered = [...jobs].sort(
      (a, b) => compare(a, b, sort.key) * (sort.dir === "asc" ? 1 : -1),
    );
    const index = ordered.findIndex((job) => job.id === revealJobId);
    if (index >= 0) setPage(Math.floor(index / pageSize) + 1);
  }, [revealJobId]);

  useEffect(() => {
    const target = revealRef.current;
    if (!target || !isVisible) return;
    const row = Array.from(
      document.querySelectorAll<HTMLElement>(".job-row"),
    ).find((item) => item.dataset.jobId === target);
    if (row) {
      const frame = requestAnimationFrame(() => {
        if (row.getClientRects().length) {
          row.scrollIntoView({ block: "nearest", behavior: "instant" });
          row.focus({ preventScroll: true });
        }
        revealRef.current = null;
      });
      return () => cancelAnimationFrame(frame);
    }
  }, [currentPage, selected, sorted.length, isVisible]);

  // A filtered list and its preview must refer to the same result set.
  // Selection alone does not open the mobile detail screen.
  useEffect(() => {
    if (loading || revealRef.current || !isVisible) return;
    if (hasOpenDetail && window.matchMedia("(max-width: 1180px)").matches) return;
    if (!filtered.some((job) => job.id === selected))
      onSelectionChange(sorted[0]?.id ?? null);
  }, [jobs, filter, search, selected, loading, isVisible, hasOpenDetail]);

  const toggle = (key: SortKey) =>
    setSort((current) =>
      current.key === key
        ? { key, dir: current.dir === "asc" ? "desc" : "asc" }
        : { key, dir: key === "created" ? "desc" : "asc" },
    );

  return (
    <section className="jobs-panel panel" aria-label="작업 목록">
      <div className="section-heading">
        <div>
          <h2>
            작업 목록{" "}
            <span className="heading-count">{loading ? "…" : jobs.length}</span>
          </h2>
        </div>
        {working.length > 0 && (
          <button className="button-danger" onClick={onStopAll}>
            전체 중지
          </button>
        )}
      </div>
      <div className="job-tools">
        <label className="sr-only" htmlFor="job-search">
          작업 검색
        </label>
        <input
          id="job-search"
          placeholder="강의명·과목·주차 검색"
          value={search}
          disabled={loading}
          onChange={(event) => setSearch(event.target.value)}
        />
        <div className="job-sortby" role="group" aria-label="정렬 순서">
          {sortOptions.map((option) => {
            const isActiveSort =
              sort.key === "created" && sort.dir === option.value;
            return (
              <button
                key={option.value}
                type="button"
                className={"segment" + (isActiveSort ? " active" : "")}
                aria-pressed={isActiveSort}
                disabled={loading}
                onClick={() =>
                  setSort({
                    key: "created",
                    dir: option.value as "asc" | "desc",
                  })
                }
              >
                {option.label}
              </button>
            );
          })}
        </div>
      </div>
      <div className="job-list">
        <div className="job-table-head">
          {columns.map((column) => (
            <span key={column.label}>
              {column.key ? (
                <button
                  type="button"
                  className="job-sort"
                  aria-label={`${column.label} 정렬${sort.key === column.key ? (sort.dir === "asc" ? " · 오름차순" : " · 내림차순") : ""}`}
                  onClick={() => toggle(column.key!)}
                >
                  {column.label}
                  <span className="job-sort-caret" aria-hidden="true">
                    {sort.key === column.key
                      ? sort.dir === "asc"
                        ? "▲"
                        : "▼"
                      : ""}
                  </span>
                </button>
              ) : (
                column.label
              )}
            </span>
          ))}
        </div>
        {loading ? (
          Array.from({ length: 6 }).map((_, index) => (
            <div
              className="job-row skeleton-row"
              key={"skeleton-" + index}
              aria-hidden="true"
            >
              <span className="skeleton sk-badge" />
              <span className="skeleton sk-name" />
              <span className="skeleton sk-sm" />
              <span className="skeleton sk-sm" />
              <span className="skeleton sk-sm" />
            </div>
          ))
        ) : sorted.length === 0 ? (
          <div className="empty">
            <span aria-hidden="true">▤</span>
            <h3>
              {jobs.length
                ? "조건에 맞는 작업이 없습니다."
                : "아직 정리한 강의가 없어요."}
            </h3>
            <p>
              {jobs.length
                ? "다른 검색어나 상태로 다시 찾아보세요."
                : "강의를 가져오면 처리 현황과 결과가 여기에 표시됩니다."}
            </p>
            {jobs.length === 0 && (
              <button className="primary" onClick={onImport}>
                강의 가져오기
              </button>
            )}
            {jobs.length > 0 && (
              <button
                className="secondary"
                onClick={() => {
                  setSearch("");
                  onFilter("all");
                }}
              >
                검색·필터 초기화
              </button>
            )}
          </div>
        ) : (
          visible.map((job) => (
            <button
              key={job.id}
              data-job-id={job.id}
              className={"job-row" + (selected === job.id ? " selected" : "")}
              aria-current={selected === job.id ? "true" : undefined}
              aria-controls="job-result"
              onClick={() => onSelect(job.id)}
            >
              <span className={"status " + job.status}>{statusText(job)}</span>
              <span className="job-name" title={job.display_name}>
                <strong>{job.display_name}</strong>
                {(job.course_name || job.week_title) && (
                  <small>
                    {[job.course_name, job.week_title]
                      .filter(Boolean)
                      .join(" · ")}
                  </small>
                )}
              </span>
              <StageMini job={job} />
              <span className="job-attempts">{job.attempts.length}</span>
              <span className="job-time" title={formatDate(job.created_at)}>
                {formatDate(job.created_at)}
              </span>
            </button>
          ))
        )}
        {!loading && sorted.length > 0 && (
          <div className="job-pager">
            <span className="job-pager-range">
              {rangeStart}–{rangeEnd} / {sorted.length}
            </span>
            <div className="job-pager-nav">
              <div
                className="job-pagesize"
                role="group"
                aria-label="페이지당 작업 수"
              >
                {pageSizes.map((size) => (
                  <button
                    key={size}
                    type="button"
                    className={"segment" + (pageSize === size ? " active" : "")}
                    aria-pressed={pageSize === size}
                    onClick={() => setPageSize(size)}
                  >
                    {size}
                  </button>
                ))}
              </div>
              <button
                type="button"
                className="pager-btn"
                onClick={() => goTo(currentPage - 1)}
                disabled={currentPage <= 1}
                aria-label="이전 페이지"
              >
                ‹
              </button>
              <span className="job-pager-page" aria-live="polite">
                {currentPage} / {pageCount}
              </span>
              <button
                type="button"
                className="pager-btn"
                onClick={() => goTo(currentPage + 1)}
                disabled={currentPage >= pageCount}
                aria-label="다음 페이지"
              >
                ›
              </button>
            </div>
          </div>
        )}
      </div>
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
                aria-expanded={playbackOpen}
                onClick={() => setPlaybackOpen?.(!playbackOpen)}
              >
                지난 재생 {playbackHistory.length}건
                <span aria-hidden="true">{playbackOpen ? "▴" : "▾"}</span>
              </button>
            )}
          </div>
          {playbackOpen && playbackHistory.length > 0 && (
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
                      "segment" +
                      (playbackFilter === option.value ? " active" : "")
                    }
                    aria-pressed={playbackFilter === option.value}
                    onClick={() => setPlaybackFilter?.(option.value)}
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
          {playbackOpen &&
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
                {(item.status === "failed" || item.status === "interrupted") &&
                  onPlaybackRetry && (
                    <button
                      type="button"
                      className="playback-link"
                      onClick={() => onPlaybackRetry(item)}
                      title="이 재생을 다시 큐에 넣습니다."
                    >
                      다시 재생
                    </button>
                  )}
                {item.job_ids && item.job_ids.length > 0 && (
                  <button
                    type="button"
                    className="playback-link"
                    onClick={() => revealJob(item.job_ids![0])}
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
    </section>
  );
}
