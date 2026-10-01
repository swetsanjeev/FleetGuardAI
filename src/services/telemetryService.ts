import { apiClient } from "../api/client";
import { TelemetryPoint } from "../types/telemetry";

export const telemetryService = {
  async latest(vin: string): Promise<TelemetryPoint[]> { return apiClient.get(`/telemetry/${vin}/latest`); },
  async history(vin: string, from: string, to: string): Promise<TelemetryPoint[]> {
    return apiClient.get(`/telemetry/${vin}/history?from=${from}&to=${to}`);
  },
};
