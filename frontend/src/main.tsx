import React, { useCallback, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import ReactMarkdown from "react-markdown";
import { api, allJobs, ApiError } from "./api";
import type {
  Artifact,
  Job,
  Settings,
  SettingsResponse,
  Upload,
} from "./types";
import "./style.css";
import { SettingsEditor } from "./SettingsEditor";
import { LMSPanel, ServerPanel, JobLogs } from "./WorkspaceExtras";

const stages = ["다운로드", "오디오 변환", "음성 인식", "요약"];
const statuses: Record<string, string> = {
  queued: "대기",
  running: "처리 중",
  cancelling: "중지 중",
  completed: "완료",
  failed: "실패",
  cancelled: "취소",
  interrupted: "중단",
};
const kinds: Record<string, string> = {
  input: "입력 원문",
  video: "영상",
  audio: "오디오",
  transcript: "STT 원문",
  summary: "요약",
  prompt: "챗봇 프롬프트",
};
const active = (job: Job) =>
  ["queued", "running", "cancelling"].includes(job.status);
const bytes = (value: number) =>
  value < 1024 ** 2
    ? (value / 1024).toFixed(1) + " KB"
    : (value / 1024 ** 2).toFixed(1) + " MB";
const formatDate = (date: string) =>
  new Intl.DateTimeFormat("ko-KR", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(date));

function App() {
  const [jobs, setJobs] = useState<Job[]>([]),
    [selected, setSelected] = useState<string | null>(null);
  const [settings, setSettings] = useState<SettingsResponse | null>(null),
    [draft, setDraft] = useState<Settings | null>(null);
  const [files, setFiles] = useState<File[]>([]),
    [uploads, setUploads] = useState<Upload[]>([]);
  const [busy, setBusy] = useState(false),
    [saving, setSaving] = useState(false),
    [pending, setPending] = useState<string | null>(null);
  const [notice, setNotice] = useState(""),
    [error, setError] = useState(""),
    [connection, setConnection] = useState("연결 중");
  const [settingsOpen, setSettingsOpen] = useState(false),
    [endStage, setEndStage] = useState(4);
  const [jobModel, setJobModel] = useState("chatgpt");
  const [text, setText] = useState(""),
    [artifact, setArtifact] = useState<Artifact | null>(null),
    [loadingText, setLoadingText] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const batchRef = useRef<{
    uploads: Upload[];
    revision: string;
    endStage: number;
    key: string;
  } | null>(null);
  const [filter, setFilter] = useState("all"),
    [search, setSearch] = useState("");
  const fileInput = useRef<HTMLInputElement>(null),
    textArea = useRef<HTMLTextAreaElement>(null);
  const seenCursor = useRef(0),
    bootRef = useRef(false),
    contentRequest = useRef(0);
  const report = (cause: unknown) =>
    setError(cause instanceof Error ? cause.message : "요청에 실패했습니다.");
  const merge = useCallback(
    (incoming: Job[]) =>
      setJobs((old) => {
        const map = new Map(old.map((job) => [job.id, job]));
        incoming.forEach((job) => {
          if (!map.has(job.id) || map.get(job.id)!.revision <= job.revision)
            map.set(job.id, job);
        });
        return [...map.values()].sort((a, b) =>
          b.created_at.localeCompare(a.created_at),
        );
      }),
    [],
  );

  useEffect(() => {
    let alive = true;
    let events: EventSource | null = null;
    let timer: ReturnType<typeof setTimeout>;
    const connect = async () => {
      try {
        const [snapshot, config] = await Promise.all([
          allJobs(),
          api<SettingsResponse>("/settings"),
        ]);
        if (!alive) return;
        merge(snapshot.jobs);
        seenCursor.current = snapshot.cursor;
        setSettings(config);
        setDraft(config.settings);
        bootRef.current = true;
        events?.close();
        events = new EventSource("/api/v1/events?cursor=" + snapshot.cursor);
        events.onopen = () => alive && setConnection("실시간 연결");
        events.onerror = () => alive && setConnection("재연결 중");
        events.addEventListener("job.updated", (event) => {
          const message = event as MessageEvent;
          const payload = JSON.parse(message.data);
          seenCursor.current = Number(message.lastEventId);
          api<Job>("/jobs/" + payload.job_id)
            .then((job) => alive && merge([job]))
            .catch(report);
        });
        events.addEventListener("reset", () => {
          events?.close();
          if (alive) void connect();
        });
        setSelected((current) => current ?? snapshot.jobs.at(-1)?.id ?? null);
      } catch (cause) {
        if (alive) {
          report(cause);
          setConnection("연결 끊김");
          timer = setTimeout(connect, 3000);
        }
      }
    };
    void connect();
    // REST reconciliation also recovers transient detail fetch failures while SSE is connected.
    const reconcile = setInterval(() => {
      if (bootRef.current)
        allJobs()
          .then((snapshot) => alive && merge(snapshot.jobs))
          .catch(() => alive && setConnection("재연결 중"));
    }, 10000);
    return () => {
      alive = false;
      events?.close();
      clearTimeout(timer);
      clearInterval(reconcile);
    };
  }, [merge]);

  const current = jobs.find((job) => job.id === selected) ?? null;
  useEffect(() => {
    let alive = true;
    setJobModel("chatgpt");
    if (current)
      api<{ settings: { ai_model: string } }>(
        "/jobs/" + current.id + "/settings",
      )
        .then((result) => {
          if (alive) setJobModel(result.settings.ai_model);
        })
        .catch(() => {});
    return () => {
      alive = false;
    };
  }, [current?.id, current?.settings_revision_id]);
  const openArtifact = useCallback(async (item: Artifact) => {
    const sequence = ++contentRequest.current;
    setArtifact(item);
    setText("");
    setLoadingText(true);
    try {
      const result = await api<{ text: string }>(
        "/artifacts/" + item.id + "/content",
      );
      if (sequence === contentRequest.current) setText(result.text);
    } catch (cause) {
      if (sequence === contentRequest.current) report(cause);
    } finally {
      if (sequence === contentRequest.current) setLoadingText(false);
    }
  }, []);
  useEffect(() => {
    contentRequest.current++;
    setArtifact(null);
    setText("");
    setLoadingText(false);
    const latest = current?.artifacts.filter(
      (item) =>
        item.state === "complete" &&
        item.attempt_id === current.current_attempt_id,
    );
    const preferred =
      latest?.find((item) => item.kind === "summary") ??
      latest?.find((item) => item.kind === "prompt") ??
      latest?.find((item) => item.kind === "transcript");
    if (preferred) void openArtifact(preferred);
  }, [current?.id, current?.current_attempt_id, current?.status, openArtifact]);

  const saveSettings = async () => {
    if (!settings || !draft) return;
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const saved = await api<SettingsResponse>("/settings", {
        method: "PATCH",
        body: JSON.stringify({
          expected_revision: settings.revision,
          settings: draft,
        }),
      });
      setSettings(saved);
      setDraft(saved.settings);
      setNotice("설정을 저장했습니다. 새로 제출하는 작업부터 적용됩니다.");
    } catch (cause) {
      report(cause);
      if (cause instanceof ApiError && cause.code === "settings_conflict") {
        const fresh = await api<SettingsResponse>("/settings");
        setSettings(fresh);
        // Preserve unsaved edits after a concurrent credential/settings update.
      }
    } finally {
      setSaving(false);
    }
  };
  const submit = async () => {
    if (!settings || !files.length) return;
    setBusy(true);
    setError("");
    setNotice("");
    const staged: Upload[] = batchRef.current?.uploads ?? [];
    let acknowledged = false;
    try {
      // A saved revision is captured before uploading; concurrent edits cannot change this batch.
      const revision = batchRef.current?.revision ?? settings.settings_revision;
      if (!batchRef.current)
        for (const file of files) {
          const reserved = await api<Upload>("/uploads", {
            method: "POST",
            body: JSON.stringify({ filename: file.name, size: file.size }),
          });
          staged.push(reserved);
          setUploads([...staged]);
          try {
            const ready = await api<Upload>(
              "/uploads/" + reserved.id + "/content",
              {
                method: "PUT",
                body: file,
                headers: { "Content-Type": "application/octet-stream" },
              },
            );
            staged[staged.length - 1] = ready;
            setUploads([...staged]);
          } catch (cause) {
            await api("/uploads/" + reserved.id, { method: "DELETE" }).catch(
              () => {},
            );
            throw cause;
          }
        }
      batchRef.current ??= {
        uploads: staged,
        revision,
        endStage,
        key: requestId(),
      };
      const batch = batchRef.current;
      const result = await api<{ job_ids: string[] }>("/jobs", {
        method: "POST",
        headers: { "Idempotency-Key": batch.key },
        body: JSON.stringify({
          sources: batch.uploads.map((item) => ({
            kind: "file",
            reference: item.id,
          })),
          settings_revision: batch.revision,
          end_stage: batch.endStage,
        }),
      });
      acknowledged = true;
      const added = await Promise.all(
        result.job_ids.map((id) => api<Job>("/jobs/" + id)),
      );
      batchRef.current = null;
      setUncertain(false);
      merge(added);
      setSelected(result.job_ids[0]);
      setFiles([]);
      setUploads([]);
      setNotice(
        `${added.length}개 작업을 추가했습니다. 이 화면을 닫아도 처리는 계속됩니다.`,
      );
    } catch (cause) {
      report(cause);
      if (batchRef.current && (!(cause instanceof ApiError) || acknowledged)) {
        setUncertain(true);
        setNotice(
          "제출 응답을 확인하지 못했습니다. 다시 확인하면 같은 요청을 이어서 조회합니다.",
        );
      } else {
        batchRef.current = null;
        setUncertain(false);
        await Promise.all(
          staged.map((item) =>
            api("/uploads/" + item.id, { method: "DELETE" }).catch(() => {}),
          ),
        );
      }
    } finally {
      setBusy(false);
    }
  };
  const command = async (job: Job, action: string) => {
    setPending(job.id);
    setError("");
    try {
      const updated = await api<Job>("/jobs/" + job.id + "/" + action, {
        method: "POST",
        headers:
          action === "retry" ? { "Idempotency-Key": requestId() } : undefined,
        body: JSON.stringify({ attempt_id: job.current_attempt_id }),
      });
      merge([updated]);
    } catch (cause) {
      report(cause);
    } finally {
      setPending(null);
    }
  };
  const stopAll = async () => {
    if (!window.confirm("현재 대기·실행 중인 작업을 모두 중지할까요?")) return;
    try {
      await api("/jobs/cancel-all", { method: "POST", body: "{}" });
      merge((await allJobs()).jobs);
    } catch (cause) {
      report(cause);
    }
  };
  const copy = async () => {
    try {
      if (!navigator.clipboard) throw new Error("manual");
      await navigator.clipboard.writeText(text);
      setNotice("클립보드에 복사했습니다.");
    } catch {
      textArea.current?.focus();
      textArea.current?.select();
      setNotice(
        "텍스트를 전체 선택했습니다. 기기의 복사 기능을 사용해 주세요.",
      );
    }
  };
  const addFiles = (list: FileList | null) => {
    if (!list) return;
    const added = Array.from(list);
    const allowed = /\.(mp4|ts|wav|mp3|txt)$/i;
    if (added.some((file) => !allowed.test(file.name) || file.size === 0)) {
      setError("비어 있지 않은 MP4, TS, WAV, MP3, TXT 파일을 선택해 주세요.");
      return;
    }
    if (added.length + files.length > 50) {
      setError("한 번에 최대 50개 파일을 선택할 수 있습니다.");
      return;
    }
    setFiles((old) => [...old, ...added]);
    setError("");
    if (fileInput.current) fileInput.current.value = "";
  };
  const working = jobs.filter(active),
    completed = jobs.filter((job) => job.status === "completed");
  const filtered = jobs.filter(
    (job) =>
      (filter === "all" ||
        (filter === "active"
          ? active(job)
          : filter === "completed"
            ? job.status === "completed"
            : job.retryable)) &&
      job.display_name.toLowerCase().includes(search.toLowerCase()),
  );
  const available =
    current?.artifacts.filter(
      (item) =>
        item.state === "complete" &&
        (item.attempt_id === current.current_attempt_id ||
          item.attempt_id === null),
    ) ?? [];
  return (
    <div className="app-shell">
      <aside className="rail">
        <a className="brand" href="/" aria-label="강의 작업실 홈">
          <span className="brand-mark">L</span>
          <span>
            LMS<span className="brand-sub">강의 작업실</span>
          </span>
        </a>
        <div className="rail-caption">YOUR LEARNING, IN ORDER</div>
        <nav aria-label="메뉴">
          <button
            className={!settingsOpen ? "nav-item selected" : "nav-item"}
            onClick={() => setSettingsOpen(false)}
          >
            <span>▤</span>작업실<span className="nav-count">{jobs.length}</span>
          </button>
          <button
            className={settingsOpen ? "nav-item selected" : "nav-item"}
            onClick={() => setSettingsOpen(true)}
          >
            <span>⚙</span>처리 설정
          </button>
        </nav>
        <div className="rail-bottom">
          <span className="connection-dot" /> {connection}
          <p>개인 서버 · 로컬 사용자</p>
        </div>
      </aside>
      <main>
        <header className="page-header">
          <div>
            <span className="eyebrow">LECTURE WORKSPACE</span>
            <h1>{settingsOpen ? "처리 설정" : "강의에서, 핵심으로."}</h1>
            <p>
              {settingsOpen
                ? "저장한 설정은 새 작업에 적용됩니다. 진행 중인 작업은 제출 당시 설정을 유지합니다."
                : "자료를 올리고, 처리 흐름을 확인하고, 핵심을 다시 읽으세요."}
            </p>
          </div>
          <span className="private-label">개인 작업실</span>
        </header>
        {error && (
          <div role="alert" className="message error">
            {error}
            <button aria-label="오류 닫기" onClick={() => setError("")}>
              ×
            </button>
          </div>
        )}
        {notice && (
          <div role="status" className="message notice">
            {notice}
            <button aria-label="안내 닫기" onClick={() => setNotice("")}>
              ×
            </button>
          </div>
        )}
        {settingsOpen && draft && settings && (
          <SettingsEditor
            draft={draft}
            setDraft={setDraft}
            settings={settings}
            onSecrets={(fresh) =>
              setSettings((old) =>
                !old || fresh.revision >= old.revision ? fresh : old,
              )
            }
            save={() => void saveSettings()}
            saving={saving}
            report={report}
          />
        )}
        <div hidden={settingsOpen}>
          <>
            <section className="overview" aria-label="작업 현황">
              <div>
                <span className="stat-number">
                  {String(working.length).padStart(2, "0")}
                </span>
                <span>처리 중인 작업</span>
              </div>
              <div>
                <span className="stat-number">
                  {String(completed.length).padStart(2, "0")}
                </span>
                <span>완료된 작업</span>
              </div>
              <div className="pipeline-summary">
                {stages.map((stage, index) => {
                  const runs = working
                    .flatMap((job) => job.attempts.at(-1)!.stages)
                    .filter((run) => run.stage === index + 1);
                  return (
                    <div key={stage}>
                      <span className="step-index">0{index + 1}</span>
                      <strong>{stage}</strong>
                      <small>
                        대기{" "}
                        {runs.filter((run) => run.status === "queued").length} ·
                        실행{" "}
                        {runs.filter((run) => run.status === "running").length}
                      </small>
                    </div>
                  );
                })}
              </div>
            </section>
            <LMSPanel
              settings={settings}
              endStage={endStage}
              setEndStage={setEndStage}
              onSubmitted={async (ids) => {
                const added = await Promise.all(
                  ids.map((id) => api<Job>("/jobs/" + id)),
                );
                merge(added);
                setSelected(ids[0]);
              }}
              report={report}
            />
            <section className="intake panel">
              <div className="intake-title">
                <span className="eyebrow">ADD MATERIAL</span>
                <h2>새로운 강의 자료</h2>
                <p>파일에 맞는 단계부터 이어서 처리합니다.</p>
              </div>
              <div className="intake-body">
                <input
                  ref={fileInput}
                  id="file-input"
                  type="file"
                  multiple
                  accept=".mp4,.ts,.wav,.mp3,.txt"
                  disabled={busy || uncertain}
                  onChange={(e) => addFiles(e.target.files)}
                  className="file-input"
                />
                <label
                  htmlFor="file-input"
                  className={
                    "drop-zone" + (busy || uncertain ? " disabled" : "")
                  }
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    if (!busy && !uncertain) addFiles(e.dataTransfer.files);
                  }}
                >
                  <span className="upload-symbol">↑</span>
                  <span>
                    <strong>파일을 놓거나 선택하세요</strong>
                    <small>영상 · 오디오 · UTF-8 텍스트</small>
                  </span>
                  <span className="file-types">MP4 / TS / WAV / MP3 / TXT</span>
                </label>
                {files.length > 0 && (
                  <ul className="file-list">
                    {files.map((file, index) => (
                      <li key={file.name + index}>
                        <span>{file.name}</span>
                        <small>
                          {bytes(file.size)} ·{" "}
                          {/\.txt$/i.test(file.name)
                            ? "요약부터"
                            : /\.(wav|mp3)$/i.test(file.name)
                              ? "음성 인식부터"
                              : "변환부터"}
                          {uploads[index]
                            ? " · " +
                              (uploads[index].status === "ready"
                                ? "업로드 완료"
                                : "업로드 중")
                            : ""}
                        </small>
                        <button
                          aria-label={file.name + " 제거"}
                          disabled={busy || uncertain}
                          onClick={() =>
                            setFiles((old) => old.filter((_, i) => i !== index))
                          }
                        >
                          ×
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
                <div className="intake-footer">
                  <label className="inline-label">
                    마지막 처리 단계
                    <select
                      aria-label="마지막 처리 단계"
                      disabled={busy || uncertain}
                      value={endStage}
                      onChange={(e) => setEndStage(Number(e.target.value))}
                    >
                      <option value={4}>요약 / 프롬프트 준비</option>
                      <option value={3}>음성 인식까지만</option>
                      <option value={2}>오디오 변환까지만</option>
                      <option value={1}>다운로드까지만 (LMS URL)</option>
                    </select>
                  </label>
                  <button
                    className="primary"
                    disabled={busy || !files.length || !settings}
                    onClick={() => void submit()}
                  >
                    {busy
                      ? "업로드·작업 추가 중…"
                      : uncertain
                        ? "제출 다시 확인 →"
                        : files.length
                          ? `${files.length}개 작업 시작 →`
                          : "작업 시작 →"}
                  </button>
                </div>
              </div>
            </section>
            <div className="workspace-grid">
              <section className="jobs-panel panel">
                <div className="section-heading">
                  <div>
                    <span className="eyebrow">PROCESSING QUEUE</span>
                    <h2>
                      작업 목록{" "}
                      <span className="heading-count">{jobs.length}</span>
                    </h2>
                  </div>
                  {working.length > 0 && (
                    <button
                      className="quiet danger"
                      onClick={() => void stopAll()}
                    >
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
                    onChange={(e) => setSearch(e.target.value)}
                  />
                  <select
                    aria-label="상태 필터"
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
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
                      <span>▤</span>
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
                        className={
                          "job-row " + (selected === job.id ? "selected" : "")
                        }
                        onClick={() => setSelected(job.id)}
                      >
                        <span
                          className={
                            "file-glyph " +
                            (job.status === "completed" ? "finished" : "")
                          }
                        >
                          {job.status === "completed" ? "✓" : "▤"}
                        </span>
                        <span className="job-row-body">
                          <strong>{job.display_name}</strong>
                          <small>
                            {formatDate(job.created_at)} ·{" "}
                            {stages[job.initial_stage - 1]}부터
                          </small>
                        </span>
                        <span className={"status " + job.status}>
                          {job.result_kind === "manual_ready"
                            ? "프롬프트 준비"
                            : statuses[job.status]}
                        </span>
                      </button>
                    ))
                  )}
                </div>
              </section>
              <section className="result-panel panel" aria-label="작업 상세">
                {current ? (
                  <>
                    <div className="section-heading">
                      <div>
                        <span className="eyebrow">WORK & RESULTS</span>
                        <h2>{current.display_name}</h2>
                      </div>
                      <span className={"status " + current.status}>
                        {current.result_kind === "manual_ready"
                          ? "프롬프트 준비 완료"
                          : statuses[current.status]}
                      </span>
                    </div>
                    <ol className="stage-track">
                      {stages.map((label, index) => {
                        const run = current.attempts
                          .at(-1)!
                          .stages.find((stage) => stage.stage === index + 1);
                        return (
                          <li key={label} className={run?.status ?? "skipped"}>
                            <span>
                              {run?.status === "completed"
                                ? "✓"
                                : String(index + 1).padStart(2, "0")}
                            </span>
                            {label}
                          </li>
                        );
                      })}
                    </ol>
                    <div className="detail-actions">
                      <small>
                        시도 {current.attempts.length}회 ·{" "}
                        {formatDate(current.created_at)}
                      </small>
                      {["queued", "running"].includes(current.status) && (
                        <button
                          disabled={pending === current.id}
                          className="quiet danger"
                          onClick={() => void command(current, "cancel")}
                        >
                          작업 취소
                        </button>
                      )}
                      {current.retryable && (
                        <button
                          disabled={pending === current.id}
                          className="secondary"
                          onClick={() => void command(current, "retry")}
                        >
                          다시 시도
                        </button>
                      )}
                    </div>
                    {current.attempts.at(-1)?.safe_message && (
                      <p className="inline-error">
                        {current.attempts.at(-1)?.safe_message}
                      </p>
                    )}
                    {current.result_kind === "manual_ready" && (
                      <p className="manual-note">
                        프롬프트가 준비되었습니다. 복사한 뒤{" "}
                        <a
                          href={
                            {
                              chatgpt: "https://chatgpt.com/",
                              "claude-web": "https://claude.ai/",
                              "gemini-web": "https://gemini.google.com/app",
                              "grok-web": "https://grok.com/",
                            }[jobModel] ?? "https://chatgpt.com/"
                          }
                          target="_blank"
                          rel="noreferrer"
                        >
                          챗봇 열기 ↗
                        </a>
                        에서 붙여넣으세요.
                      </p>
                    )}
                    {available.length > 0 ? (
                      <>
                        <div
                          className="artifact-tabs"
                          role="group"
                          aria-label="결과 파일"
                        >
                          {available.map((item) => (
                            <button
                              key={item.id}
                              className={
                                artifact?.id === item.id ? "active" : ""
                              }
                              onClick={() => void openArtifact(item)}
                              disabled={!item.display_name.endsWith(".txt")}
                            >
                              {kinds[item.kind] ?? item.kind}
                            </button>
                          ))}
                        </div>
                        <div className="file-downloads">
                          {available
                            .filter(
                              (item) => !item.display_name.endsWith(".txt"),
                            )
                            .map((item) => (
                              <a
                                key={item.id}
                                href={
                                  "/api/v1/artifacts/" + item.id + "/download"
                                }
                                download
                              >
                                {kinds[item.kind]} 다운로드 ↓
                              </a>
                            ))}
                        </div>
                        {artifact && (
                          <div className="reader">
                            <div className="reader-toolbar">
                              <span>
                                {kinds[artifact.kind]} · {bytes(artifact.size)}
                              </span>
                              <div>
                                <button
                                  className="quiet"
                                  disabled={loadingText || !text}
                                  onClick={() => void copy()}
                                >
                                  복사
                                </button>
                                <a
                                  className="quiet"
                                  href={
                                    "/api/v1/artifacts/" +
                                    artifact.id +
                                    "/download"
                                  }
                                  download
                                >
                                  다운로드 ↓
                                </a>
                              </div>
                            </div>
                            {loadingText ? (
                              <p className="reader-empty" role="status">
                                결과를 불러오는 중…
                              </p>
                            ) : artifact.kind === "summary" ? (
                              <div className="markdown">
                                <ReactMarkdown>{text}</ReactMarkdown>
                              </div>
                            ) : null}
                            <label
                              className={
                                artifact.kind === "summary" ? "sr-only" : ""
                              }
                              htmlFor="result-text"
                            >
                              {artifact.kind === "summary"
                                ? "요약 원문"
                                : "원문 · 전체 선택하여 복사할 수 있습니다."}
                            </label>
                            <textarea
                              id="result-text"
                              ref={textArea}
                              className={
                                artifact.kind === "summary"
                                  ? "source-text"
                                  : "result-text"
                              }
                              readOnly
                              value={text}
                              rows={12}
                            />
                          </div>
                        )}
                        {!artifact && (
                          <div className="file-downloads">
                            {available.map((item) => (
                              <a
                                key={item.id}
                                href={
                                  "/api/v1/artifacts/" + item.id + "/download"
                                }
                                download
                              >
                                {kinds[item.kind]} 다운로드 ↓
                              </a>
                            ))}
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="empty result-empty">
                        <span>↗</span>
                        <h3>
                          {active(current)
                            ? "차근차근 처리하고 있습니다."
                            : "이 작업에는 아직 결과가 없습니다."}
                        </h3>
                        <p>
                          {active(current)
                            ? "결과가 준비되면 이곳에 표시됩니다."
                            : "실패·취소·중단된 작업은 다시 시도할 수 있습니다."}
                        </p>
                      </div>
                    )}
                    <JobLogs job={current} />
                    <details className="attempt-history">
                      <summary>시도 이력</summary>
                      {current.attempts.map((attempt) => (
                        <p key={attempt.id}>
                          시도 {attempt.number} · {statuses[attempt.status]}{" "}
                          {attempt.safe_message
                            ? "· " + attempt.safe_message
                            : ""}
                        </p>
                      ))}
                    </details>
                  </>
                ) : (
                  <div className="empty result-empty">
                    <span>↗</span>
                    <h3>결과를 읽는 공간</h3>
                    <p>
                      작업을 선택하면 처리 단계와
                      <br />
                      원문·요약을 함께 확인할 수 있습니다.
                    </p>
                  </div>
                )}
              </section>
            </div>
          </>
        </div>
        <ServerPanel report={report} />
        <footer className="page-footer">
          <span>LMS SUMMARIZER</span>
          <span>화면을 닫아도 서버의 작업은 계속됩니다.</span>
        </footer>
      </main>
    </div>
  );
}
function requestId() {
  return Array.from(crypto.getRandomValues(new Uint8Array(16)), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
