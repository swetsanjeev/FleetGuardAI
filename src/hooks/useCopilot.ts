import { useState } from "react";
import { copilotService } from "../services/copilotService";

export interface CopilotMessage { role: "user" | "assistant"; content: string }

export function useCopilot() {
  const [messages, setMessages] = useState<CopilotMessage[]>([]);
  async function send(content: string) {
    setMessages((m) => [...m, { role: "user", content }]);
    const reply = await copilotService.ask(content).catch(() => "(offline)");
    setMessages((m) => [...m, { role: "assistant", content: reply }]);
  }
  return { messages, send };
}
