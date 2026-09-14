// Thin client for the FastAPI backend. The chat endpoint streams NDJSON, which
// streamChat yields one parsed event at a time.

export function demoKey() {
  try { return localStorage.getItem("xenovia-demo-key") || ""; } catch { return ""; }
}
export function saveKey(k) {
  try { localStorage.setItem("xenovia-demo-key", k); } catch { /* ignore */ }
}
function headers() {
  const h = { "content-type": "application/json" };
  const k = demoKey();
  if (k) h["x-demo-key"] = k;
  return h;
}

export async function fetchRoster() {
  const res = await fetch("/api/agents", { headers: headers() });
  return res.json();
}

export async function resetSession(session) {
  if (!session) return;
  try {
    await fetch("/api/reset", { method: "POST", headers: headers(), body: JSON.stringify({ session }) });
  } catch { /* best effort */ }
}

export async function* streamChat({ agent, session, message, mode }) {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ agent, session, message, mode }),
  });
  if (!res.ok) {
    let body = {};
    try { body = await res.json(); } catch { /* ignore */ }
    const err = new Error(body.error || res.statusText);
    err.status = res.status;
    err.error = body.error;
    throw err;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, idx).trim();
      buffer = buffer.slice(idx + 1);
      if (line) yield JSON.parse(line);
    }
  }
}
