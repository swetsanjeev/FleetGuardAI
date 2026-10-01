import { apiClient } from "../api/client";

export const analyticsService = {
  async kpis(): Promise<Record<string, number>> { return apiClient.get("/analytics/kpis"); },
  async fleetUtilization(): Promise<Record<string, number>> { return apiClient.get("/analytics/utilization"); },
};
