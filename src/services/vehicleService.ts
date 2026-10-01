import { apiClient } from "../api/client";
import { Vehicle } from "../types/vehicle";

export const vehicleService = {
  async list(): Promise<Vehicle[]> { return apiClient.get("/vehicles"); },
  async get(vin: string): Promise<Vehicle> { return apiClient.get(`/vehicles/${vin}`); },
  async updateTelemetryConfig(vin: string, hz: number) { return apiClient.put(`/vehicles/${vin}/telemetry`, { hertz: hz }); },
};
