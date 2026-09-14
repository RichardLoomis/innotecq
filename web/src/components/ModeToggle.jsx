// Two modes for the same LangChain agent, differing only in the base URL the
// model call goes to: through the Xenovia proxy (governed) or straight to the
// model (no proxy). The toggle is the demo's before/after.
export default function ModeToggle({ mode, modes, onChange }) {
  return (
    <div className="regime" role="group" aria-label="Routing mode">
      <button
        className="r-gov"
        aria-pressed={mode === "proxy"}
        disabled={!modes.proxy}
        title={modes.proxy ? "Route via the Xenovia proxy" : "Set XENOVIA_BASE_URL to enable"}
        onClick={() => onChange("proxy")}
      >
        <span className="dot" />Xenovia
      </button>
      <button
        className="r-ungov"
        aria-pressed={mode === "direct"}
        disabled={!modes.direct}
        title={modes.direct ? "Call the model directly, no proxy" : "Set DIRECT_BASE_URL to enable"}
        onClick={() => onChange("direct")}
      >
        <span className="dot" />Direct
      </button>
    </div>
  );
}
