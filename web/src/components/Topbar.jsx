import RegimeToggle from "./RegimeToggle.jsx";
import { splitTitle } from "../util.js";

export default function Topbar({ agent, mode, modes, onMode, onReset }) {
  const t = splitTitle(agent.title);
  return (
    <div className="topbar">
      <div className="title">
        <h1>{t.name} {t.episode && <span className="ep">{t.episode}</span>}</h1>
      </div>
      <div className="spacer" />
      <RegimeToggle mode={mode} modes={modes} onChange={onMode} />
      <button className="reset" onClick={onReset}>Reset</button>
    </div>
  );
}
