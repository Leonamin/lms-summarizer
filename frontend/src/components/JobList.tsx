import { useState } from "react";
import type { Job } from "../types";
import { formatDate, isActive, stages, statusText } from "../lib/format";

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
        <select
          aria-label="상태 필터"
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
        >
          <option value="all">전체 작업</option>
          <option value="active">처리 중</option>
          <option value="completed">완료</option>
          <option value="retryable">실패·취소·중단</option>
        </select>
      </div>
      <div className="job-list">
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
              <span
                className={
                  "file-glyph" + (job.status === "completed" ? " finished" : "")
                }
                aria-hidden="true"
              >
                {job.status === "completed" ? "✓" : "▤"}
              </span>
              <span className="job-row-body">
                <strong>{job.display_name}</strong>
                <small>
                  {formatDate(job.created_at)} · {stages[job.initial_stage - 1]}
                  부터
                </small>
              </span>
              <span className={"status " + job.status}>{statusText(job)}</span>
            </button>
          ))
        )}
      </div>
    </section>
  );
}
