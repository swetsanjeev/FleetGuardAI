import { apiClient } from "../api/client";

export const maintenanceService = {
  async workOrders(): Promise<any[]> { return apiClient.get("/maintenance/work-orders"); },
  async predict(vin: string) { return apiClient.get(`/maintenance/predict/${vin}`); },
};
