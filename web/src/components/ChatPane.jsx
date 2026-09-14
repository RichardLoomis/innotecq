import { useState } from "react";
import Topbar from "./Topbar.jsx";
import Hero from "./Hero.jsx";
import Thread from "./Thread.jsx";
import Composer from "./Composer.jsx";
import { host } from "../util.js";

function statusText(mode, modes, endpoints) {
  if (mode === "governed" && modes.governed) {
    return {
      sub: `Every action is decided by <b>Xenovia</b> — tenant ${host(endpoints.governed)}. Denials and traces appear in your tenant console.`,
      hint: "Enter to send · Shift+Enter for a new line · replies are live, <b>governed by Xenovia</b>",
    };
  }
  if (mode === "ungoverned" && modes.ungoverned) {
    return {
      sub: "No policy layer attached — <b>every action the model requests will execute.</b>",
      hint: "Enter to send · Shift+Enter for a new line · replies are live, <b>ungoverned</b>",
    };
  }
  return {
    sub: "No endpoint configured. Set XENOVIA_BASE_URL (and optionally UNGOVERNED_BASE_URL) on the service.",
    hint: "Configure an endpoint to start chatting.",
  };
}

export default function ChatPane({ agent, thread, mode, modes, endpoints, onSend }) {
  const [draft, setDraft] = useState("");
  const configured = modes[mode];
  const busy = thread.busy;
  const { sub, hint } = statusText(mode, modes, endpoints);

  function submit() {
    const text = draft.trim();
    if (!text || busy || !configured) return;
    setDraft("");
    onSend(text);
  }

  const composer = {
    value: draft,
    onChange: setDraft,
    onSend: submit,
    disabled: !configured || busy,
    placeholder: configured ? "How can I help you today?" : "Configure an endpoint to start chatting",
    hint,
  };

  return (
    <main className="chat">
      <Topbar agent={agent} />
      <div className="substatus" dangerouslySetInnerHTML={{ __html: sub }} />
      <div className="stage">
        {thread.started ? (
          <Thread items={thread.items} busy={busy} />
        ) : (
          <Hero agent={agent} composer={composer} onStarter={(s) => !busy && configured && onSend(s)} />
        )}
      </div>
      {thread.started && (
        <div className="dock">
          <Composer {...composer} />
        </div>
      )}
    </main>
  );
}
