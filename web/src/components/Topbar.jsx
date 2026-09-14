import { splitTitle } from "../util.js";

export default function Topbar({ agent, onReset }) {
  const t = splitTitle(agent.title);
  return (
    <div className="topbar">
      <div className="title">
        <h1>{t.name} {t.episode && <span className="ep">{t.episode}</span>}</h1>
      </div>
      <div className="spacer" />
      <button className="reset" onClick={onReset}>Reset</button>
    </div>
  );
}
