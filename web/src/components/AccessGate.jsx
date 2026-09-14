import { useState } from "react";

export default function AccessGate({ onSubmit, showError }) {
  const [value, setValue] = useState("");
  return (
    <div className="gate-screen">
      <div className="gate">
        <h2>Access key required</h2>
        <p>This console starts live agent conversations. Enter the demo access key to continue.</p>
        <form onSubmit={(e) => { e.preventDefault(); onSubmit(value.trim()); }}>
          <input
            type="password"
            autoComplete="off"
            aria-label="Demo access key"
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
          <button type="submit">Unlock</button>
        </form>
        {showError && <div className="bad">That key was not accepted.</div>}
      </div>
    </div>
  );
}
