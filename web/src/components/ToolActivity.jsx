import { useState } from "react";
import { fmtArgs } from "../util.js";

function Result({ text }) {
  const [open, setOpen] = useState(false);
  const clampable = text.length > 200;
  return (
    <div
      className={"res" + (clampable && !open ? " clamp" : "")}
      title={clampable ? "Click to expand" : undefined}
      onClick={() => clampable && setOpen((o) => !o)}
    >
      {text}
    </div>
  );
}

// One grouped "machine tape" block per turn: the agent's tool calls and their
// results, in order. Border tint records the regime the turn ran under.
export default function ToolActivity({ regime, lines }) {
  return (
    <div className={"activity " + regime}>
      {lines.map((line, i) => {
        if (line.type === "call") {
          return (
            <div className="call" key={i}>
              ▸ <b>{line.name}</b>({fmtArgs(line.args)})
            </div>
          );
        }
        if (line.type === "err") {
          return <div className="err" key={i}>{line.text}</div>;
        }
        return <Result text={line.text} key={i} />;
      })}
    </div>
  );
}
