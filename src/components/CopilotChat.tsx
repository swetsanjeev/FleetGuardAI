import React, { useState } from "react";
import { useCopilot } from "../hooks/useCopilot";

export function CopilotChat() {
  const [input, setInput] = useState("");
  const { messages, send } = useCopilot();
  return (
    <div className="copilot-chat">
      <ul>{messages.map((m, i) => <li key={i}>{m.role}: {m.content}</li>)}</ul>
      <input value={input} onChange={(e) => setInput(e.target.value)} />
      <button onClick={() => { send(input); setInput(""); }}>Ask</button>
    </div>
  );
}
