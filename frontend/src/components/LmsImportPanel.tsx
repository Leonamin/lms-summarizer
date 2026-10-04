import { useCourseCatalog } from "../hooks/useCourseCatalog";
import { CoursePicker } from "./CoursePicker";
import type { CourseSource } from "../lib/courses";
import { endStageOptions } from "../lib/processingOptions";
import { useRef, useState } from "react";
import { api, ApiError } from "../api";
import type { SettingsResponse } from "../types";
import { requestId } from "../lib/format";
import { Dropdown } from "./Dropdown";

export function LmsImportPanel({
  mode,
  onSettings,
  settings,
  endStage,
  setEndStage,
  onSubmitted,
  report,
}: {
  mode: "urls" | "courses";
  onSettings: () => void;
  settings: SettingsResponse | null;
  endStage: number;
  setEndStage: (stage: number) => void;
  onSubmitted: (ids: string[]) => Promise<void>;
  report: (cause: unknown) => void;
}) {
  const [urls, setUrls] = useState("");
  const catalog = useCourseCatalog(settings, report);
  const { setSelected, query, message, setMessage } = catalog;
  const [isSubmitting, setIsSubmitting] = useState(false);
  const isBusy = isSubmitting || catalog.isRefreshing;
  const [isUncertain, setIsUncertain] = useState(false);
  const batch = useRef<{
    sources: { kind: string; reference: string }[];
    settings_revision: string;
    end_stage: number;
    key: string;
  } | null>(null);
  async function submit(items: CourseSource[]) {
    if (!settings || (!items.length && !batch.current)) return;
    setIsSubmitting(true);
    setMessage("");
    let isAcknowledged = false;
    try {
      batch.current ??= {
        sources: items.map((item) => ({ kind: "url", ...item })),
        settings_revision: settings.settings_revision,
        end_stage: endStage,
        key: requestId(),
      };
      const { key, ...body } = batch.current;
      const result = await api<{ job_ids: string[] }>("/jobs", {
        method: "POST",
        body: JSON.stringify(body),
        headers: { "Idempotency-Key": key },
      });
      isAcknowledged = true;
      await onSubmitted(result.job_ids);
      batch.current = null;
      setIsUncertain(false);
      setSelected([]);
      setUrls("");
      setMessage(result.job_ids.length + "개 URL 작업을 추가했습니다.");
    } catch (cause) {
      report(cause);
      if (cause instanceof ApiError && !isAcknowledged) {
        batch.current = null;
        setIsUncertain(false);
      } else {
        setIsUncertain(true);
        setMessage(
          "제출 응답을 확인하지 못했습니다. 같은 요청으로 다시 확인해 주세요.",
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  const urlLines = urls.split(/\s+/).filter(Boolean);

  return (
    <section className="panel lms-panel">
      <div className="section-heading">
        <div>
          <h2>{mode === "courses" ? "과목·주차에서 선택" : "강의 URL 입력"}</h2>
          <p className="muted">
            {mode === "courses"
              ? "과목을 고르고 가져올 강의를 선택하세요."
              : "강의 링크를 한 줄에 하나씩 입력하세요."}
          </p>
        </div>
      </div>
      {settings &&
        (!settings.settings.student_id ||
          !settings.secrets.lms_password?.configured) && (
          <p className="manual-note">
            LMS에서 가져오려면 처리 설정에 학번과 비밀번호를 저장하세요.
          </p>
        )}
      <div className="course-tools">
        <button className="quiet" onClick={onSettings}>
          LMS 계정·처리 설정 →
        </button>
        <label>
          LMS 마지막 처리 단계
          <Dropdown
            value={String(endStage)}
            onChange={(value) => setEndStage(Number(value))}
            options={endStageOptions}
            ariaLabel="LMS 마지막 처리 단계"
            disabled={isBusy || isUncertain}
          />
        </label>
      </div>
      {message && (
        <p role="status" className="manual-note">
          {message}
        </p>
      )}
      {query && ["queued", "running"].includes(query.status) && (
        <p role="status" className="muted">
          목록 조회 {query.status === "queued" ? "대기 중" : "실행 중"} ·
          새로고침해도 조회는 계속됩니다.
        </p>
      )}
      <div hidden={mode !== "urls"}>
        <label>
          LMS 강의 URL
          <textarea
            rows={3}
            value={urls}
            disabled={isBusy || isUncertain}
            onChange={(event) => setUrls(event.target.value)}
            placeholder="https://canvas.ssu.ac.kr/courses/… (한 줄에 하나)"
          />
        </label>
        <div className="form-footer">
          <small>Canvas LMS URL · 최대 50개 · 실행 중 추가 가능</small>
          <button
            className="primary"
            disabled={
              isBusy ||
              (!urlLines.length && !isUncertain) ||
              urlLines.length > 50 ||
              !settings
            }
            onClick={() =>
              void submit(urlLines.map((reference) => ({ reference })))
            }
          >
            {isBusy
              ? "제출 중…"
              : isUncertain
                ? "제출 결과 다시 확인"
                : urlLines.length + "개 URL 작업 추가"}
          </button>
        </div>
      </div>
      <div hidden={mode !== "courses"}>
        <CoursePicker
          catalog={catalog}
          isSubmitting={isSubmitting}
          isUncertain={isUncertain}
          hasSettings={!!settings}
          onSubmit={(sources) => void submit(sources)}
        />
      </div>
    </section>
  );
}
