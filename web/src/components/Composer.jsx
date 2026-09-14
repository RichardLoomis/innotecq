import { useEffect, useRef } from "react";

export default function Composer({ value, onChange, onSend, disabled, placeholder, hint }) {
  const ref = useRef(null);

  useEffect(() => {
    const ta = ref.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 168) + "px";
  }, [value]);

  function keyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  }

  return (
    <div className="composer-wrap">
      <div className="composer">
        <textarea
          ref={ref}
          rows={1}
          value={value}
          placeholder={placeholder}
          aria-label="Message the agent"
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={keyDown}
        />
        <button className="send" aria-label="Send" disabled={disabled || !value.trim()} onClick={onSend}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 19V5M6 11l6-6 6 6" />
          </svg>
        </button>
      </div>
      {hint && <div className="composer-hint" dangerouslySetInnerHTML={{ __html: hint }} />}
    </div>
  );
}
