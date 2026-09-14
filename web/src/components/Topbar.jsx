import ModeToggle from "./ModeToggle.jsx";
import { splitTitle } from "../util.js";

export default function Topbar({ agent, mode, modes, onMode }) {
  const t = splitTitle(agent.title);
  return (
    <div className="topbar">
      <div className="title">
        <h1>{t.name}</h1>
      </div>
      <div className="spacer" />
      <ModeToggle mode={mode} modes={modes} onChange={onMode} />
    </div>
  );
}
