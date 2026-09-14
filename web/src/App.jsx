import { useEffect, useReducer, useRef, useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import ChatPane from "./components/ChatPane.jsx";
import AccessGate from "./components/AccessGate.jsx";
import { fetchRoster, login, saveKey, streamChat } from "./api.js";
import { uid } from "./util.js";

const newThread = () => ({ items: [], sessionId: null, busy: false, started: false, incidents: 0 });

const SYS_NOTE = {
  gov: "Review this agent's policy pack in Xenovia.",
  ungov: "These actions ran with no policy layer.",
};

function reducer(state, a) {
  const t = state[a.key];
  switch (a.type) {
    case "init":
      return a.threads;
    case "session":
      return { ...state, [a.key]: { ...t, sessionId: a.sessionId } };
    case "start":
      return { ...state, [a.key]: { ...t, started: true } };
    case "busy":
      return { ...state, [a.key]: { ...t, busy: a.busy } };
    case "append":
      return { ...state, [a.key]: { ...t, items: [...t.items, a.item] } };
    case "activity": {
      const items = [...t.items];
      const last = items[items.length - 1];
      if (last && last.kind === "activity" && !last.closed) {
        items[items.length - 1] = { ...last, lines: [...last.lines, a.line] };
      } else {
        items.push({ id: uid(), kind: "activity", regime: a.regime, closed: false, lines: [a.line] });
      }
      return { ...state, [a.key]: { ...t, items } };
    }
    case "closeActivity": {
      const items = t.items.map((it) => (it.kind === "activity" && !it.closed ? { ...it, closed: true } : it));
      return { ...state, [a.key]: { ...t, items } };
    }
    case "incidents": {
      const items = [...t.items];
      for (const text of a.items) items.push({ id: uid(), kind: "incident", text });
      items.push({ id: uid(), kind: "sysnote", text: SYS_NOTE[a.regime] });
      return { ...state, [a.key]: { ...t, items, incidents: t.incidents + a.items.length } };
    }
    case "reset":
      return { ...state, [a.key]: newThread() };
    default:
      return state;
  }
}

export default function App() {
  const [roster, setRoster] = useState(null);
  const [gateError, setGateError] = useState(false);
  const [mode, setMode] = useState("proxy");
  const [currentKey, setCurrentKey] = useState(null);
  const [threads, dispatch] = useReducer(reducer, {});
  const threadsRef = useRef(threads);
  threadsRef.current = threads;
  const modeRef = useRef(mode);
  modeRef.current = mode;

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  async function load() {
    const r = await fetchRoster();
    setRoster(r);
    if (r.gated && !r.authorized) return;  // show the gate; no error until an attempt fails
    dispatch({ type: "init", threads: Object.fromEntries(r.agents.map((a) => [a.key, newThread()])) });
    setCurrentKey((k) => k || r.agents[0]?.key);
  }

  useEffect(() => {
    document.body.dataset.regime = mode;
  }, [mode]);

  // Each agent has its own gateway, so modes are per-agent. When the selected
  // mode isn't available for the current agent, fall back to the other.
  useEffect(() => {
    if (!roster) return;
    const m = roster.agents.find((a) => a.key === currentKey)?.modes || {};
    if (!m[mode] && (m.proxy || m.direct)) setMode(m.proxy ? "proxy" : "direct");
  }, [currentKey, roster]); // eslint-disable-line react-hooks/exhaustive-deps

  async function send(key, text) {
    const t = threadsRef.current[key];
    if (!t || t.busy) return;
    const regime = modeRef.current === "proxy" ? "gov" : "ungov";
    if (!t.started) dispatch({ type: "start", key });
    dispatch({ type: "busy", key, busy: true });
    dispatch({ type: "append", key, item: { id: uid(), kind: "user", text } });
    try {
      for await (const ev of streamChat({ agent: key, session: t.sessionId, message: text, mode: modeRef.current })) {
        switch (ev.type) {
          case "session": dispatch({ type: "session", key, sessionId: ev.id }); break;
          case "assistant": dispatch({ type: "append", key, item: { id: uid(), kind: "assistant", text: ev.text } }); break;
          case "tool_call": dispatch({ type: "activity", key, regime, line: { type: "call", name: ev.name, args: ev.args } }); break;
          case "tool_result": dispatch({ type: "activity", key, regime, line: { type: "result", text: ev.result } }); break;
          case "final": dispatch({ type: "closeActivity", key }); dispatch({ type: "append", key, item: { id: uid(), kind: "final", text: ev.text } }); break;
          case "error":
          case "turn_limit": dispatch({ type: "activity", key, regime, line: { type: "err", text: ev.message } }); break;
          case "incidents": dispatch({ type: "incidents", key, regime, items: ev.items }); break;
          default: break;
        }
      }
    } catch (err) {
      dispatch({ type: "append", key, item: { id: uid(), kind: "sysnote", text: "Not sent. " + (err.error || err.message || "HTTP " + err.status) } });
    } finally {
      dispatch({ type: "closeActivity", key });
      dispatch({ type: "busy", key, busy: false });
    }
  }

  async function unlock(key) {
    const { ok } = await login(key);
    if (!ok) { setGateError(true); return; }
    saveKey(key);
    setGateError(false);
    await load();
  }

  if (!roster) return null;
  if (roster.gated && !roster.authorized) return <AccessGate onSubmit={unlock} showError={gateError} />;

  const agent = roster.agents.find((a) => a.key === currentKey);
  if (!agent) return null;
  const thread = threads[currentKey] || newThread();

  return (
    <div className="shell">
      <Sidebar
        agents={roster.agents}
        currentKey={currentKey}
        threads={threads}
        onSelect={setCurrentKey}
      />
      <ChatPane
        key={currentKey}
        agent={agent}
        thread={thread}
        mode={mode}
        modes={agent.modes}
        onMode={setMode}
        onSend={(text) => send(currentKey, text)}
      />
    </div>
  );
}
