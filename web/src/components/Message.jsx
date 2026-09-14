export default function Message({ role, text }) {
  if (role === "user") return <div className="msg-user">{text}</div>;
  return <div className={"msg-agent" + (role === "interim" ? " interim" : "")}>{text}</div>;
}
