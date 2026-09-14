// The before/after switch at the heart of the demo. Governed routes every model
// call through Xenovia (teal); Ungoverned goes straight to the raw model (amber).
export default function RegimeToggle({ mode, modes, onChange }) {
  return (
    <div className="regime" role="group" aria-label="Governance regime">
      <button
        className="r-ungov"
        aria-pressed={mode === "ungoverned"}
        disabled={!modes.ungoverned}
        title={modes.ungoverned ? "" : "Set UNGOVERNED_BASE_URL to enable"}
        onClick={() => onChange("ungoverned")}
      >
        <span className="dot" />Ungoverned
      </button>
      <button
        className="r-gov"
        aria-pressed={mode === "governed"}
        disabled={!modes.governed}
        title={modes.governed ? "" : "Set XENOVIA_BASE_URL to enable"}
        onClick={() => onChange("governed")}
      >
        <span className="dot" />Governed
      </button>
    </div>
  );
}
