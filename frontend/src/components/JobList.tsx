import { useJobList } from "../hooks/useJobList";
import type { SortKey } from "../lib/jobList";
import type { ReactNode } from "react";
import type { Job } from "../types";
import { formatDate, type JobFilter, statusText } from "../lib/format";
import { StageMini } from "./StageMini";

const sortOptions = [
  { value: "desc", label: "최신순" },
  { value: "asc", label: "과거순" },
];

const pageSizes = [10, 20];

const columns: { key: SortKey | null; label: string }[] = [
  { key: "status", label: "상태" },
  { key: "name", label: "이름" },
  { key: null, label: "단계" },
  { key: "attempts", label: "시도" },
  { key: "created", label: "만든 시각" },
];

export function JobList({
  children,
  jobs,
  filter,
  onFilter,
  revealRequest,
  onImport,
  isVisible,
  hasOpenDetail,
  selected,
  onSelect,
  onSelectionChange,
  onStopAll,
  isLoading = false,
}: {
  children?: ReactNode;
  jobs: Job[];
  filter: JobFilter;
  onFilter: (filter: JobFilter) => void;
  revealRequest: { id: string } | null;
  onImport: () => void;
  isVisible: boolean;
  hasOpenDetail: boolean;
  selected: string | null;
  onSelect: (id: string) => void;
  onSelectionChange: (id: string | null) => void;
  onStopAll: () => void;
  isLoading?: boolean;
}) {
  const {
    search,
    setSearch,
    sort,
    setSort,
    pageSize,
    setPageSize,
    working,
    sorted,
    visible,
    currentPage,
    pageCount,
    rangeStart,
    rangeEnd,
    goTo,
    toggle,
  } = useJobList({
    jobs,
    filter,
    onFilter,
    revealRequest,
    isVisible,
    hasOpenDetail,
    selected,
    onSelectionChange,
    isLoading,
  });

  return (
    <section className="jobs-panel panel" aria-label="작업 목록">
      <div className="section-heading">
        <div>
          <h2>
            작업 목록{" "}
            <span className="heading-count">
              {isLoading ? "…" : jobs.length}
            </span>
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
          disabled={isLoading}
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
                disabled={isLoading}
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
        {isLoading ? (
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
        {!isLoading && sorted.length > 0 && (
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
      {children}
    </section>
  );
}
