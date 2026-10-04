import type { Job } from "../types";
export type SortKey = "status" | "name" | "attempts" | "created";

export const compareJobs = (a: Job, b: Job, key: SortKey) => {
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

export type JobSort = { key: SortKey; dir: "asc" | "desc" };
export function sortJobs(jobs: Job[], sort: JobSort): Job[] {
  return [...jobs].sort(
    (a, b) => compareJobs(a, b, sort.key) * (sort.dir === "asc" ? 1 : -1),
  );
}
export function getJobPage(
  jobs: Job[],
  id: string,
  sort: JobSort,
  pageSize: number,
): number | null {
  const index = sortJobs(jobs, sort).findIndex((job) => job.id === id);
  return index < 0 ? null : Math.floor(index / pageSize) + 1;
}
