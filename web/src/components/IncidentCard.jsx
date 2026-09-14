// The one place red appears: an action that executed and that a Xenovia policy
// pack would have denied or escalated.
export default function IncidentCard({ text }) {
  return (
    <div className="incident">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
        <path d="M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
      </svg>
      <span>{text}</span>
    </div>
  );
}
