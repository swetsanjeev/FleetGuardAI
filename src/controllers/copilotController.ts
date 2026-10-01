import { copilotService } from "../services/copilotService";

export async function askCopilot(prompt: string) { return copilotService.ask(prompt); }
