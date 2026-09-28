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

export function JobList({
  jobs,
  selected,
  onSelect,
  onStopAll,
}: {
  jobs: Job[];
  selected: string | null;
  onSelect: (id: string) => void;
  onStopAll: () => void;
}) {
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
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

  return (
    <section className="jobs-panel panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">PROCESSING QUEUE</span>
          <h2>
            작업 목록 <span className="heading-count">{jobs.length}</span>
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
          onChange={(event) => setSearch(event.target.value)}
        />
        <Dropdown
          value={filter}
          onChange={setFilter}
          options={filterOptions}
          ariaLabel="상태 필터"
          className="job-filter"
        />
      </div>
      <div className="job-list">
        <div className="job-table-head" aria-hidden="true">
          <span>상태</span>
          <span>이름</span>
          <span>시작</span>
          <span>만든 시각</span>
        </div>
        {filtered.length === 0 ? (
          <div className="empty">
            <span aria-hidden="true">▤</span>
            <h3>
              {jobs.length
                ? "조건에 맞는 작업이 없습니다."
                : "아직 정리한 강의가 없어요."}
            </h3>
            <p>
              {jobs.length
                ? "검색 조건을 바꿔보세요."
                : "위에서 첫 자료를 선택해 주세요."}
            </p>
          </div>
        ) : (
          filtered.map((job) => (
            <button
              key={job.id}
              className={"job-row" + (selected === job.id ? " selected" : "")}
              aria-current={selected === job.id}
              onClick={() => onSelect(job.id)}
            >
              <span className={"status " + job.status}>{statusText(job)}</span>
              <span className="job-name">{job.display_name}</span>
              <span className="job-stage">{stages[job.initial_stage - 1]}</span>
              <span className="job-time">{formatDate(job.created_at)}</span>
            </button>
          ))
        )}
      </div>
    </section>
  );
}
