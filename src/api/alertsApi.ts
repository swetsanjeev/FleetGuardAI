import { apiClient } from "./client";

export const alertsApi = { list: () => apiClient.get("/alerts") };
