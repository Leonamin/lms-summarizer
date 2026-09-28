import { useEffect, useState } from "react";
import { api } from "../api";

type SystemInfo = {
  version: string;
  sqlite_version: string;
  free_bytes: number;
  chrome_available: boolean;
  health: { running: boolean; error_code: string | null };
  stage_counts: Record<string, unknown>;
  runtime: { chrome_mode: string; local_stt_device: string };
};

type UpdateInfo = {
  status: string;
  latest?: string;
  newer?: boolean;
  url?: string;
};

export function ServerPanel({ report }: { report: (cause: unknown) => void }) {
  const [system, setSystem] = useState<SystemInfo | null>(null);
  const [update, setUpdate] = useState<UpdateInfo | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      setSystem(await api<SystemInfo>("/system"));
    } catch (cause) {
      report(cause);
    }
  }
  useEffect(() => {
    void load();
  }, []);

  async function check() {
    setBusy(true);
    try {
      setUpdate(
        await api<UpdateInfo>("/system/update-check", {
          method: "POST",
          body: "{}",
        }),
      );
    } catch (cause) {
      report(cause);
    } finally {
      setBusy(false);
    }
  }

  return (
    <details className="panel server-panel">
      <summary>서버 진단 · 버전 · 업데이트</summary>
      <div className="diagnostic-grid">
        <div>
          <h3>실행 상태</h3>
          <p>
            버전 {system?.version ?? "확인 중"} · SQLite{" "}
            {system?.sqlite_version ?? "—"}
          </p>
          <p>
            작업 서비스 {system?.health.running ? "실행 중" : "확인 필요"} ·
            Chrome {system?.chrome_available ? "사용 가능" : "경로 확인 필요"}
          </p>
          <p>
            여유 공간{" "}
            {system ? (system.free_bytes / 1024 ** 3).toFixed(1) + " GiB" : "—"}
          </p>
          <button className="ghost" onClick={() => void load()}>
            진단 새로고침
          </button>
        </div>
        <div>
          <h3>서버 실행 · 저장</h3>
          <p>
            시스템 Chrome · {system?.runtime.chrome_mode ?? "확인 중"} / 로컬
            STT · {system?.runtime.local_stt_device ?? "CPU 기본"}
          </p>
          <p>
            데이터와 모델은 별도 서버 볼륨에 저장합니다. 기기 폴더 열기는 결과
            다운로드로 제공합니다.
          </p>
          <p>
            Chrome 경로·화면 모드는 서버 실행 설정입니다. 접속 기기 경로를
            사용하지 않습니다.
          </p>
        </div>
        <div>
          <h3>업데이트 안내</h3>
          <button
            className="secondary"
            disabled={busy}
            onClick={() => void check()}
          >
            {busy ? "확인 중…" : "최신 릴리즈 확인"}
          </button>
          {update && (
            <p role="status">
              {update.status === "unavailable"
                ? "릴리즈를 확인하지 못했습니다. 나중에 다시 확인해 주세요."
                : update.newer
                  ? `새 버전 ${update.latest}`
                  : `최신 확인: ${update.latest}`}
              {update.url && (
                <>
                  {" "}
                  ·{" "}
                  <a href={update.url} target="_blank" rel="noreferrer">
                    릴리즈 보기 ↗
                  </a>
                </>
              )}
            </p>
          )}
          <p>데이터·모델 볼륨을 백업한 뒤 서버에서 실행하세요.</p>
          <code>docker compose up -d --build</code>
          <p>화면에서 앱을 자동 교체하지 않습니다.</p>
        </div>
      </div>
    </details>
  );
}
