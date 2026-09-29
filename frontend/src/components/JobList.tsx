import { useEffect, useState } from "react";
import type { Job, Playback } from "../types";
import { formatDate, isActive, stages, statusText } from "../lib/format";
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

const pageSizes = [10, 20];

type SortKey = "status" | "name" | "attempts" | "created";

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
}: {
  jobs: Job[];
  playbacks?: Playback[];
  selected: string | null;
  onSelect: (id: string) => void;
  onStopAll: () => void;
  loading?: boolean;
}) {
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<{ key: SortKey; dir: "asc" | "desc" }>({
    key: "created",
    dir: "desc",
  });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
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
            const active =
              sort.key === "created" && sort.dir === option.value;
            return (
              <button
                key={option.value}
                type="button"
                className={"segment" + (active ? " active" : "")}
                aria-pressed={active}
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
          <div className="playback-group">
            <div className="playback-group-head">
              <span className="eyebrow">AUTO PLAY</span>
              <small>자동 감지 재생 · 학습 완료용 별도 큐</small>
            </div>
            {playbacks.map((item) => (
              <div className="job-row playback-row" key={item.id}>
                <span
                  className={
                    "status " + (item.status === "running" ? "running" : "queued")
                  }
                >
                  {item.status === "running" ? "재생 중" : "재생 대기"}
                </span>
                <span className="job-name">
                  {item.title || item.lecture_url}
                </span>
                <span className="stage-mini playback-mini" aria-hidden="true">
                  재생
                </span>
                <span className="job-attempts">-</span>
                <span className="job-time">{formatDate(item.created_at)}</span>
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
