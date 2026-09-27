import type { View } from "../lib/format";

export function Rail({
  view,
  setView,
  jobCount,
  connection,
}: {
  view: View;
  setView: (view: View) => void;
  jobCount: number;
  connection: string;
}) {
  return (
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
          className={"nav-item" + (view === "workspace" ? " selected" : "")}
          aria-current={view === "workspace"}
          onClick={() => setView("workspace")}
        >
          <span aria-hidden="true">▤</span>작업실
          <span className="nav-count">{jobCount}</span>
        </button>
        <button
          className={"nav-item" + (view === "settings" ? " selected" : "")}
          aria-current={view === "settings"}
          onClick={() => setView("settings")}
        >
          <span aria-hidden="true">⚙</span>처리 설정
        </button>
      </nav>
      <div className="rail-bottom">
        <span className="connection-dot" aria-hidden="true" /> {connection}
        <p>개인 서버 · 로컬 사용자</p>
      </div>
    </aside>
  );
}
