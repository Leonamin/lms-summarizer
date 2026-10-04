import type { Job } from "../types";

export type View = "workspace" | "import" | "settings";
export type JobFilter = "all" | "active" | "completed" | "retryable";
export const stages = ["다운로드", "오디오 변환", "음성 인식", "요약"];
export const statusLabels: Record<string, string> = {
  queued: "대기",
  running: "처리 중",
  cancelling: "취소 중",
  completed: "완료",
  failed: "실패",
  cancelled: "취소",
  interrupted: "중단",
};
export const playbackStatusLabels: Record<string, string> = {
  ...statusLabels,
  running: "재생 중",
  playing: "재생 중",
};
export const kindLabels: Record<string, string> = {
  source: "영상",
  video: "영상",
  audio: "오디오",
  transcript: "STT 원문",
  summary: "요약",
  prompt: "프롬프트",
};
export const attendanceLabels: Record<string, string> = {
  attendance: "출석",
  late: "지각",
  absent: "결석",
  excused: "출석 인정",
  none: "미출석",
};
export const completionLabels: Record<string, string> = {
  completed: "학습 완료",
  complete: "학습 완료",
  incomplete: "미완료",
  in_progress: "학습 중",
  not_started: "학습 전",
  unknown: "진도 미확인",
};
export const chatbotUrls: Record<string, string> = {
  chatgpt: "https://chatgpt.com/",
  "gemini-web": "https://gemini.google.com/app",
  "claude-web": "https://claude.ai/",
  "grok-web": "https://grok.com/",
};
export const isActive = (job: Job): boolean =>
  ["queued", "running", "cancelling"].includes(job.status);
export const isPlaybackActive = (status: string): boolean =>
  ["queued", "running", "playing"].includes(status);
export const isPlaybackIncomplete = (status: string): boolean =>
  ["failed", "interrupted"].includes(status);
export const statusText = (job: Job): string =>
  job.status === "completed" && job.result_kind === "manual_ready"
    ? "프롬프트 준비"
    : (statusLabels[job.status] ?? job.status);
export const isJobInFilter = (job: Job, filter: JobFilter): boolean =>
  filter === "all" ||
  (filter === "active"
    ? isActive(job)
    : filter === "completed"
      ? job.status === "completed"
      : job.retryable);
export function formatDate(value: string): string {
  return new Date(value).toLocaleString("ko-KR", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
export function bytes(size: number): string {
  if (size < 1024) return `${size} B`;
  const unit = Math.min(Math.floor(Math.log(size) / Math.log(1024)), 3);
  return `${(size / 1024 ** unit).toFixed(1)} ${["B", "KB", "MB", "GB"][unit]}`;
}
/** LAN HTTP does not expose randomUUID; getRandomValues is still available. */
export function requestId(): string {
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
  const data = crypto.getRandomValues(new Uint8Array(16));
  data[6] = (data[6] & 0x0f) | 0x40;
  data[8] = (data[8] & 0x3f) | 0x80;
  const hex = Array.from(data, (value) =>
    value.toString(16).padStart(2, "0"),
  ).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}
