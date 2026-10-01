import { apiClient } from "./client";

export const telemetryApi = {
  latest: (vin: string) => apiClient.get(`/telemetry/${vin}/latest`),
  history: (vin: string, from: string, to: string) => apiClient.get(`/telemetry/${vin}/history?from=${from}&to=${to}`),
};
