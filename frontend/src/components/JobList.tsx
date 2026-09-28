import { useState } from "react";
import type { Job } from "../types";
import { formatDate, isActive, stages, statusText } from "../lib/format";
import { Dropdown } from "./Dropdown";

const filterOptions = [
  { value: "all", label: "전체 작업" },
  { value: "active", label: "처리 중" },
  { value: "completed", label: "완료" },
  { value: "retryable", label: "실패·취소·중단" },
];

type SortKey = "status" | "name" | "stage" | "attempts" | "created";

const columns: { key: SortKey; label: string }[] = [
  { key: "status", label: "상태" },
  { key: "name", label: "이름" },
  { key: "stage", label: "시작" },
  { key: "attempts", label: "시도" },
  { key: "created", label: "만든 시각" },
];

const compare = (a: Job, b: Job, key: SortKey) => {
  switch (key) {
    case "name":
      return a.display_name.localeCompare(b.display_name);
    case "status":
      return a.status.localeCompare(b.status);
    case "stage":
      return a.initial_stage - b.initial_stage;
    case "attempts":
      return a.attempts.length - b.attempts.length;
    default:
      return a.created_at.localeCompare(b.created_at);
  }
};

export function JobList({
  jobs,
  selected,
  onSelect,
  onStopAll,
  loading = false,
}: {
  jobs: Job[];
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
      </div>
      <div className="job-list">
        <div className="job-table-head" role="row">
          {columns.map((column) => (
            <span
              key={column.key}
              role="columnheader"
              aria-sort={
                sort.key === column.key
                  ? sort.dir === "asc"
                    ? "ascending"
                    : "descending"
                  : "none"
              }
            >
              <button
                type="button"
                className="job-sort"
                onClick={() => toggle(column.key)}
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
          sorted.map((job) => (
            <button
              key={job.id}
              className={"job-row" + (selected === job.id ? " selected" : "")}
              aria-current={selected === job.id}
              onClick={() => onSelect(job.id)}
            >
              <span className={"status " + job.status}>{statusText(job)}</span>
              <span className="job-name">{job.display_name}</span>
              <span className="job-stage">{stages[job.initial_stage - 1]}</span>
              <span className="job-attempts">{job.attempts.length}</span>
              <span className="job-time">{formatDate(job.created_at)}</span>
            </button>
          ))
        )}
      </div>
    </section>
  );
}
