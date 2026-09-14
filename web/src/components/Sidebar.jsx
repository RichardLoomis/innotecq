import { CODES, splitTitle } from "../util.js";

export default function Sidebar({ agents, currentKey, threads, mode, onSelect }) {
  return (
    <nav className="sidebar">
      <div className="brand">
        <span className="mark" />
        <span className="name">Xenovia<span> · console</span></span>
      </div>
      <div className="side-label">Agents</div>
      {agents.map((agent) => {
        const t = splitTitle(agent.title);
        const incidents = threads[agent.key]?.incidents || 0;
        return (
          <button
            key={agent.key}
            className="agent-item"
            aria-current={agent.key === currentKey}
            onClick={() => onSelect(agent.key)}
          >
            <span className="tile">{CODES[agent.key] || "··"}</span>
            <span className="meta">
              <span className="name">{t.name}</span>
            </span>
            {incidents > 0 && <span className="count">{incidents}</span>}
          </button>
        );
      })}
      <div className="sidebar-foot">
        <b>{mode === "governed" ? "Governed by Xenovia" : "Ungoverned"}</b>
      </div>
    </nav>
  );
}
