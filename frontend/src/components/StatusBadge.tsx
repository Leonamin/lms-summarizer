import type { Job } from "../types";
import { statusText } from "../lib/format";

export function StatusBadge({ job }: { job: Job }) {
  return <span className={"status " + job.status}>{statusText(job)}</span>;
}
