import { ArrowDownToLine, AudioLines, Mic, Sparkles } from "lucide-react";

export const stageIcons = [ArrowDownToLine, AudioLines, Mic, Sparkles];
export const stageRunLabels: Record<string, string> = {
  queued: "대기",
  running: "처리 중",
  completed: "완료",
  failed: "실패",
  cancelled: "취소",
  interrupted: "중단",
  skipped: "미실행",
};
export const stageSlotClass = (status?: string): string =>
  ["failed", "cancelled", "interrupted"].includes(status ?? "")
    ? "failed"
    : (status ?? "skipped");
