import { useState } from "react";
import Topbar from "./Topbar.jsx";
import Hero from "./Hero.jsx";
import Thread from "./Thread.jsx";
import Composer from "./Composer.jsx";

function statusText(mode, modes) {
  if (mode === "governed" && modes.governed) {
    return { sub: "Governed by <b>Xenovia</b>", hint: "Enter to send" };
  }
  if (mode === "ungoverned" && modes.ungoverned) {
    return { sub: "<b>Ungoverned</b>", hint: "Enter to send" };
  }
  return { sub: "No endpoint configured", hint: "" };
}

export default function ChatPane({ agent, thread, mode, modes, onSend }) {
  const [draft, setDraft] = useState("");
  const configured = modes[mode];
  const busy = thread.busy;
  const { sub, hint } = statusText(mode, modes);

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
