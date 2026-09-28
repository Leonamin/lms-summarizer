import { useCallback, useEffect, useRef, useState } from "react";
import { api, allJobs, ApiError } from "./api";
import type { Job, Settings, SettingsResponse } from "./types";
import { requestId, type View } from "./lib/format";
import { MessageBanner } from "./components/MessageBanner";
import { Rail } from "./components/Rail";
import { ServerPanel } from "./components/ServerPanel";
import { SettingsPage } from "./pages/SettingsPage";
import { WorkspacePage } from "./pages/WorkspacePage";

export function App() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [draft, setDraft] = useState<Settings | null>(null);
  const [view, setView] = useState<View>("workspace");
  const [saving, setSaving] = useState(false);
  const [pending, setPending] = useState<string | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [connection, setConnection] = useState("연결 중");
  const [ready, setReady] = useState(false);
  const [retryKey, setRetryKey] = useState(0);
  const [railCollapsed, setRailCollapsed] = useState(() => {
    try {
      return localStorage.getItem("lms-rail") === "collapsed";
    } catch {
      return false;
    }
  });
  const toggleRail = () =>
    setRailCollapsed((collapsed) => {
      const next = !collapsed;
      try {
        localStorage.setItem("lms-rail", next ? "collapsed" : "expanded");
      } catch {
        /* storage may be unavailable */
      }
      return next;
    });
  const seenCursor = useRef(0);
  const bootRef = useRef(false);

  const report = useCallback((cause: unknown) => {
    setError(cause instanceof Error ? cause.message : "요청에 실패했습니다.");
  }, []);

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
        setDraft((old) => old ?? config.settings);
        bootRef.current = true;
        setReady(true);
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
  }, [merge, report, retryKey]);

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

  const command = async (job: Job, action: "cancel" | "retry") => {
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

  const continueJob = async (job: Job, endStage: number) => {
    setPending(job.id);
    setError("");
    try {
      const updated = await api<Job>("/jobs/" + job.id + "/continue", {
        method: "POST",
        headers: { "Idempotency-Key": requestId() },
        body: JSON.stringify({
          attempt_id: job.current_attempt_id,
          end_stage: endStage,
        }),
      });
      merge([updated]);
      setNotice("이어서 처리를 시작했습니다. 남은 단계를 실행합니다.");
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

  return (
    <div className={"app-shell" + (railCollapsed ? " rail-collapsed" : "")}>
      <Rail
        view={view}
        setView={setView}
        jobCount={jobs.length}
        connection={connection}
        collapsed={railCollapsed}
        onToggle={toggleRail}
      />
      <main>
        <header className="page-header">
          <div>
            <span className="eyebrow">
              {view === "settings" ? "PREFERENCES" : "LECTURE WORKSPACE"}
            </span>
            <h1>{view === "settings" ? "처리 설정" : "강의에서, 핵심으로."}</h1>
            <p>
              {view === "settings"
                ? "저장한 설정은 새 작업에 적용됩니다. 진행 중인 작업은 제출 당시 설정을 유지합니다."
                : "자료를 올리고, 처리 흐름을 확인하고, 핵심을 다시 읽으세요."}
            </p>
          </div>
          <span className="private-label">개인 작업실</span>
        </header>
        <MessageBanner
          error={error}
          notice={notice}
          onDismiss={(kind) => (kind === "error" ? setError("") : setNotice(""))}
        />
        {connection === "연결 끊김" && (
          <div className="server-banner" role="alert">
            <span className="server-banner-icon" aria-hidden="true">
              !
            </span>
            <div className="server-banner-body">
              <strong>서버에 연결하지 못했습니다.</strong>
              <small>자동으로 다시 연결을 시도합니다.</small>
            </div>
            <button
              className="ghost"
              onClick={() => {
                setConnection("연결 중");
                setRetryKey((count) => count + 1);
              }}
            >
              다시 연결
            </button>
          </div>
        )}
        <div hidden={view === "settings"}>
          <WorkspacePage
            jobs={jobs}
            settings={settings}
            merge={merge}
            report={report}
            pending={pending}
            loading={!ready}
            onNotice={setNotice}
            onCommand={(job, action) => void command(job, action)}
            onContinue={(job, stage) => void continueJob(job, stage)}
            onStopAll={() => void stopAll()}
          />
        </div>
        {view === "settings" && draft && settings && (
          <SettingsPage
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
        <ServerPanel report={report} />
        <footer className="page-footer">
          <span>LMS SUMMARIZER</span>
          <span>화면을 닫아도 서버의 작업은 계속됩니다.</span>
        </footer>
      </main>
    </div>
  );
}
