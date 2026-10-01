import { alertService } from "../services/alertService";

export async function listAlerts() { return alertService.list(); }
export async function ackAlert(id: string) { return alertService.acknowledge(id); }
