import type { View } from "../lib/format";
import { LayoutList, Plus, Settings, type LucideIcon } from "lucide-react";

const items: { key: View; icon: LucideIcon; label: string }[] = [
  { key: "workspace", icon: LayoutList, label: "작업실" },
  { key: "import", icon: Plus, label: "강의 가져오기" },
  { key: "settings", icon: Settings, label: "처리 설정" },
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
        <a className="brand" href="#workspace" aria-label="강의 작업실 홈">
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
          aria-controls="rail-nav"
          title={collapsed ? "메뉴 펼치기" : "메뉴 접기"}
          onClick={onToggle}
        >
          {collapsed ? "»" : "«"}
        </button>
      </div>
      <div className="rail-caption">나의 강의</div>
      <nav id="rail-nav" aria-label="메뉴">
        {items.map((item) => (
          <button
            key={item.key}
            className={"nav-item" + (view === item.key ? " selected" : "")}
            aria-current={view === item.key ? "page" : undefined}
            title={item.label}
            onClick={() => setView(item.key)}
          >
            <item.icon size={18} aria-hidden="true" />
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
