import { useState } from "react";
import Topbar from "./Topbar.jsx";
import Hero from "./Hero.jsx";
import Thread from "./Thread.jsx";
import Composer from "./Composer.jsx";

export default function ChatPane({ agent, thread, mode, modes, onMode, onSend }) {
  const [draft, setDraft] = useState("");
  const configured = modes[mode];
  const busy = thread.busy;
  const hint = configured ? "Enter to send" : "";

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
      <Topbar agent={agent} mode={mode} modes={modes} onMode={onMode} />
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
