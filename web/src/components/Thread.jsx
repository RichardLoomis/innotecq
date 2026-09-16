import { useEffect, useRef } from "react";
import Message from "./Message.jsx";
import ToolActivity from "./ToolActivity.jsx";
import IncidentCard from "./IncidentCard.jsx";
import BlockedCard from "./BlockedCard.jsx";

function Thinking() {
  return <div className="thinking"><i /><i /><i /></div>;
}

export default function Thread({ items, busy }) {
  const bottom = useRef(null);
  useEffect(() => { bottom.current?.scrollIntoView({ block: "end" }); }, [items, busy]);

  return (
    <div className="threads">
      <div className="thread active">
        <div className="thread-inner">
          {items.map((it) => {
            switch (it.kind) {
              case "user": return <Message key={it.id} role="user" text={it.text} />;
              case "assistant": return <Message key={it.id} role="interim" text={it.text} />;
              case "final": return <Message key={it.id} role="agent" text={it.text} />;
              case "activity": return <ToolActivity key={it.id} regime={it.regime} lines={it.lines} />;
              case "incident": return <IncidentCard key={it.id} text={it.text} />;
              case "blocked": return <BlockedCard key={it.id} regime={it.regime} reason={it.reason} />;
              case "sysnote": return <div className="sysnote" key={it.id}>{it.text}</div>;
              default: return null;
            }
          })}
          {busy && <Thinking />}
          <div ref={bottom} />
        </div>
      </div>
    </div>
  );
}
