import { useEffect, useRef, useState } from "react";
import type { Job } from "../types";
import { isActive, isJobInFilter, type JobFilter } from "../lib/format";
import {
  getJobPage,
  sortJobs,
  type JobSort,
  type SortKey,
} from "../lib/jobList";
export type JobListStateProps = {
  jobs: Job[];
  filter: JobFilter;
  onFilter: (filter: JobFilter) => void;
  revealRequest: { id: string } | null;
  isVisible: boolean;
  hasOpenDetail: boolean;
  selected: string | null;
  onSelectionChange: (id: string | null) => void;
  isLoading: boolean;
};
export function useJobList({
  jobs,
  filter,
  onFilter,
  revealRequest,
  isVisible,
  hasOpenDetail,
  selected,
  onSelectionChange,
  isLoading,
}: JobListStateProps) {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<JobSort>({
    key: "created",
    dir: "desc",
  });
  const [pageSize, setPageSize] = useState(20);
  const criteria = JSON.stringify([
    filter,
    search,
    sort.key,
    sort.dir,
    pageSize,
  ]);
  const [pagination, setPagination] = useState({ criteria, page: 1 });
  const revealRef = useRef<{ id: string; criteria: string } | null>(null);
  useEffect(() => {
    setPagination((previous) =>
      previous.criteria === criteria ? previous : { criteria, page: 1 },
    );
  }, [criteria]);
  const working = jobs.filter(isActive);
  const filtered = jobs.filter(
    (job) =>
      isJobInFilter(job, filter) &&
      [job.display_name, job.course_name, job.week_title]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  const sorted = sortJobs(filtered, sort);

  // Bind the page to its query. A reveal can change both atomically, without
  // a later filter-reset effect overwriting the requested destination page.
  const pageCount = Math.max(1, Math.ceil(sorted.length / pageSize));
  const currentPage = Math.min(
    pagination.criteria === criteria ? pagination.page : 1,
    pageCount,
  );
  const start = (currentPage - 1) * pageSize;
  const visible = sorted.slice(start, start + pageSize);
  const goTo = (next: number) =>
    setPagination({ criteria, page: Math.min(Math.max(next, 1), pageCount) });
  const rangeStart = sorted.length === 0 ? 0 : start + 1;
  const rangeEnd = Math.min(start + pageSize, sorted.length);

  const handledRequest = useRef<{ id: string } | null>(null);
  useEffect(() => {
    if (!revealRequest || handledRequest.current === revealRequest) return;
    handledRequest.current = revealRequest;
    const targetPage = getJobPage(jobs, revealRequest.id, sort, pageSize);
    if (targetPage === null) {
      revealRef.current = null;
      return;
    }
    const nextCriteria = JSON.stringify([
      "all",
      "",
      sort.key,
      sort.dir,
      pageSize,
    ]);
    revealRef.current = { id: revealRequest.id, criteria: nextCriteria };
    onFilter("all");
    setSearch("");
    setPagination({ criteria: nextCriteria, page: targetPage });
  }, [revealRequest, jobs, sort, pageSize, onFilter]);

  useEffect(() => {
    const target = revealRef.current;
    if (!target || !isVisible || target.criteria !== criteria) return;
    const row = Array.from(
      document.querySelectorAll<HTMLElement>(".job-row"),
    ).find((item) => item.dataset.jobId === target.id);
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
  }, [
    currentPage,
    selected,
    sorted.length,
    isVisible,
    revealRequest,
    criteria,
  ]);

  // A filtered list and its preview must refer to the same result set.
  // Selection alone does not open the mobile detail screen.
  useEffect(() => {
    if (isLoading || revealRef.current || !isVisible) return;
    if (hasOpenDetail && window.matchMedia("(max-width: 1180px)").matches)
      return;
    if (!filtered.some((job) => job.id === selected))
      onSelectionChange(sorted[0]?.id ?? null);
  }, [jobs, filter, search, selected, isLoading, isVisible, hasOpenDetail]);

  const toggle = (key: SortKey) =>
    setSort((current) =>
      current.key === key
        ? { key, dir: current.dir === "asc" ? "desc" : "asc" }
        : { key, dir: key === "created" ? "desc" : "asc" },
    );

  return {
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
  };
}
