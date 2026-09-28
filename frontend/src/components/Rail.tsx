import type { View } from "../lib/format";

const items: { key: View; icon: string; label: string }[] = [
  { key: "workspace", icon: "▤", label: "작업실" },
  { key: "settings", icon: "⚙", label: "처리 설정" },
];

export function Rail({
  view,
  setView,
  jobCount,
  connection,
  collapsed,
  onToggle,
}: {
  view: View;
  setView: (view: View) => void;
  jobCount: number;
  connection: string;
  collapsed: boolean;
  onToggle: () => void;
}) {
  return (
    <aside className={"rail" + (collapsed ? " collapsed" : "")}>
      <div className="rail-head">
        <a className="brand" href="/" aria-label="강의 작업실 홈">
          <span className="brand-mark">L</span>
          <span className="brand-text">
            LMS<span className="brand-sub">강의 작업실</span>
          </span>
        </a>
        <button
          type="button"
          className="rail-toggle"
          aria-label={collapsed ? "메뉴 펼치기" : "메뉴 접기"}
          aria-expanded={!collapsed}
          title={collapsed ? "메뉴 펼치기" : "메뉴 접기"}
          onClick={onToggle}
        >
          {collapsed ? "»" : "«"}
        </button>
      </div>
      <div className="rail-caption">YOUR LEARNING, IN ORDER</div>
      <nav aria-label="메뉴">
        {items.map((item) => (
          <button
            key={item.key}
            className={"nav-item" + (view === item.key ? " selected" : "")}
            aria-current={view === item.key}
            title={item.label}
            onClick={() => setView(item.key)}
          >
            <span aria-hidden="true">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
            {item.key === "workspace" && (
              <span className="nav-count">{jobCount}</span>
            )}
          </button>
        ))}
      </nav>
      <div className="rail-bottom">
        <span className="connection-dot" aria-hidden="true" />
        <span className="rail-conn">{connection}</span>
        <p>개인 서버 · 로컬 사용자</p>
      </div>
    </aside>
  );
}
