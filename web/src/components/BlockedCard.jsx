// A gateway policy block (e.g. Xenovia's 403). This is the governance payoff,
// not an error — styled in the regime accent, never red.
export default function BlockedCard({ regime, reason }) {
  const gov = regime === "gov";
  return (
    <div className={"blocked " + (gov ? "gov" : "ungov")}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <path d="M9 12l2 2 4-4" />
      </svg>
      <div>
        <div className="b-title">{gov ? "Blocked by Xenovia" : "Request blocked"}</div>
        {reason && <div className="b-reason">{reason}</div>}
      </div>
    </div>
  );
}
