import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Job } from "../types";

type LogRow = {
  seq: number;
  type: string;
  timestamp: string;
  message?: string;
  stage?: number;
  status?: string;
};

const labels: Record<string, string> = {
  stage_started: "단계 시작",
  stage_completed: "단계 완료",
  queued: "대기",
  running: "실행",
  completed: "완료",
  failed: "실패",
  cancelled: "취소",
  interrupted: "중단",
  cancelling: "취소 요청",
};

export function JobLogs({ job }: { job: Job }) {
  const cursor = useRef(0);
  const [logs, setLogs] = useState<LogRow[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    let alive = true;
    setLogs([]);
    setError("");
    cursor.current = 0;
    const load = () =>
      api<{ logs: LogRow[]; next_cursor: number }>(
        "/jobs/" + job.id + "/logs?limit=200&cursor=" + cursor.current,
      )
        .then((result) => {
          if (alive) {
            cursor.current = result.next_cursor;
            setLogs((old) =>
              [
                ...old,
                ...result.logs.filter((row) => !old.some((o) => o.seq === row.seq)),
              ].slice(-200),
            );
            setError("");
          }
        })
        .catch(() => alive && setError("로그를 불러오지 못했습니다."));
    void load();
    const timer = setInterval(load, 3000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [job.id]);
  return (
    <details className="attempt-history">
      <summary>작업 로그 · 최근 200개</summary>
      {error && <p role="status">{error}</p>}
      <ol className="job-logs">
        {logs.map((row) => (
          <li key={row.seq}>
            <time>{new Date(row.timestamp).toLocaleTimeString("ko-KR")}</time>
            <span>
              {row.stage ? "단계 " + row.stage + " · " : ""}
              {labels[row.message ?? row.status ?? ""] ?? row.type}
            </span>
          </li>
        ))}
      </ol>
      {!logs.length && !error && (
        <p>저장된 로그가 없습니다. 로그는 7일 동안 보관합니다.</p>
      )}
    </details>
  );
}
