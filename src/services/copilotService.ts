import { apiClient } from "../api/client";

export const copilotService = {
  async ask(prompt: string): Promise<string> {
    const res = await apiClient.post("/copilot/ask", { prompt });
    return res?.answer ?? "No answer";
  },
};
