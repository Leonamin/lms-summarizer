import type { Job } from "./types";
export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
  ) {
    super(message);
  }
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && typeof options.body === "string")
    headers.set("Content-Type", "application/json");
  const response = await fetch("/api/v1" + path, { ...options, headers });
  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({
        error: {
          code: "connection_error",
          message: "서버 응답을 확인할 수 없습니다.",
        },
      }));
    throw new ApiError(body.error.code, body.error.message);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
export async function allJobs(): Promise<{ jobs: Job[]; cursor: number }> {
  const jobs: Job[] = [];
  let after = 0;
  let cursor = 0;
  while (true) {
    const page = await api<{
      jobs: Job[];
      next_cursor: number;
      event_cursor: number;
    }>("/jobs?limit=200&cursor=" + after);
    // The first page cursor predates all subsequent snapshots, so SSE cannot miss an update.
    if (!jobs.length) cursor = page.event_cursor;
    jobs.push(...page.jobs);
    if (page.jobs.length < 200) return { jobs, cursor };
    after = page.next_cursor;
  }
}
