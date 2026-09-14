import Composer from "./Composer.jsx";
import { GREETING, splitTitle } from "../util.js";

// Empty-state for an agent with no conversation yet: centered greeting, the
// composer, and starter chips — matching app.xenovia.io's home surface.
export default function Hero({ agent, composer, onStarter }) {
  const t = splitTitle(agent.title);
  return (
    <div className="hero">
      <div className="hero-head">
        <h2>{GREETING[agent.key] || "Chat with " + t.name}</h2>
        <p>{agent.tagline} The backend is a dummy system seeded with live bait — just ask.</p>
      </div>
      <div className="hero-slot">
        <Composer {...composer} />
      </div>
      <div className="chips">
        {agent.starters.map((s, i) => (
          <button className="chip" key={i} disabled={composer.disabled} onClick={() => onStarter(s)}>
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
