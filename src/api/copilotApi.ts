import { apiClient } from "./client";

export const copilotApi = { ask: (prompt: string) => apiClient.post("/copilot/ask", { prompt }) };
