import { apiClient } from "../api/client";
import { Alert } from "../types/alert";

export const alertService = {
  async list(): Promise<Alert[]> { return apiClient.get("/alerts"); },
  async acknowledge(id: string) { return apiClient.post(`/alerts/${id}/ack`, {}); },
};
