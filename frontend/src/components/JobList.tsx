import { useEffect, useRef, useState } from "react";
import type { Job, Playback } from "../types";
import {
  formatDate,
  isActive,
  isPlaybackActive,
  isPlaybackIncomplete,
  playbackStatusLabels,
  stages,
  statusText,
} from "../lib/format";
import { stageIcons, stageRunLabels, stageSlotClass } from "../lib/stageIcons";
import { Dropdown } from "./Dropdown";

const filterOptions = [
  { value: "all", label: "전체 작업" },
  { value: "active", label: "처리 중" },
  { value: "completed", label: "완료" },
  { value: "retryable", label: "실패·취소·중단" },
];

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
  playbacks = [],
  selected,
  onSelect,
  onStopAll,
  loading = false,
  playbackOpen = false,
  setPlaybackOpen,
  playbackFilter = "all",
  setPlaybackFilter,
}: {
  jobs: Job[];
  playbacks?: Playback[];
  selected: string | null;
  onSelect: (id: string) => void;
  onStopAll: () => void;
  loading?: boolean;
  playbackOpen?: boolean;
  setPlaybackOpen?: (open: boolean) => void;
  playbackFilter?: PlaybackFilter;
  setPlaybackFilter?: (filter: PlaybackFilter) => void;
}) {
  const [filter, setFilter] = useState("all");
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
      (filter === "all" ||
        (filter === "active"
          ? isActive(job)
          : filter === "completed"
            ? job.status === "completed"
            : job.retryable)) &&
      job.display_name.toLowerCase().includes(search.toLowerCase()),
  );
  const sorted = [...filtered].sort(
    (a, b) => compare(a, b, sort.key) * (sort.dir === "asc" ? 1 : -1),
  );

  // Return to the first page whenever the result set or its order changes.
  useEffect(() => {
    setPage(1);
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
    setFilter("all");
    setSearch("");
    const ordered = [...jobs].sort(
      (a, b) => compare(a, b, sort.key) * (sort.dir === "asc" ? 1 : -1),
    );
    const index = ordered.findIndex((job) => job.id === id);
    if (index >= 0) setPage(Math.floor(index / pageSize) + 1);
    revealRef.current = id;
    onSelect(id);
  };

  useEffect(() => {
    const target = revealRef.current;
    if (!target) return;
    const row = document.querySelector<HTMLElement>(
      '.job-row[data-job-id="' + target + '"]',
    );
    if (row) {
      row.scrollIntoView({ block: "nearest", behavior: "smooth" });
      revealRef.current = null;
    }
  }, [currentPage, selected, sorted.length]);

  const toggle = (key: SortKey) =>
    setSort((current) =>
      current.key === key
        ? { key, dir: current.dir === "asc" ? "desc" : "asc" }
        : { key, dir: key === "created" ? "desc" : "asc" },
    );

  return (
    <section className="jobs-panel panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">PROCESSING QUEUE</span>
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
          placeholder="파일 이름으로 찾기"
          value={search}
          disabled={loading}
          onChange={(event) => setSearch(event.target.value)}
        />
        <Dropdown
          value={filter}
          onChange={setFilter}
          options={filterOptions}
          ariaLabel="상태 필터"
          disabled={loading}
          className="job-filter"
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
        <div className="job-table-head" role="row">
          {columns.map((column) => (
            <span
              key={column.label}
              role="columnheader"
              aria-sort={
                column.key && sort.key === column.key
                  ? sort.dir === "asc"
                    ? "ascending"
                    : "descending"
                  : "none"
              }
            >
              {column.key ? (
                <button
                  type="button"
                  className="job-sort"
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
        {playbacks.length > 0 && (
          <div className="playback-group" id="playback-group">
            <div className="playback-group-head">
              <span className="eyebrow">AUTO PLAY</span>
              <small>자동 감지 재생 · 학습 완료용 별도 큐</small>
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
                <div className="job-sortby" role="group" aria-label="재생 이력 필터">
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
                <span className="playback-count">{playbackFiltered.length}건</span>
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
          </div>
        )}
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
                : "위에서 첫 자료를 선택해 주세요."}
            </p>
            {jobs.length > 0 && (
              <button
                className="secondary"
                onClick={() => {
                  setSearch("");
                  setFilter("all");
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
              aria-current={selected === job.id}
              onClick={() => onSelect(job.id)}
            >
              <span className={"status " + job.status}>{statusText(job)}</span>
              <span className="job-name" title={job.display_name}>
                {job.display_name}
              </span>
              <StageMini job={job} />
              <span className="job-attempts">{job.attempts.length}</span>
              <span className="job-time">{formatDate(job.created_at)}</span>
            </button>
          ))
        )}
        {!loading && sorted.length > 0 && (
          <div className="job-pager">
            <span className="job-pager-range">
              {rangeStart}–{rangeEnd} / {sorted.length}
            </span>
            <div className="job-pager-nav">
              <div className="job-pagesize" role="group" aria-label="페이지당 작업 수">
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
    </section>
  );
}
