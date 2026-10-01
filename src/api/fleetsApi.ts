import { apiClient } from "./client";

export const fleetsApi = { list: () => apiClient.get("/fleets") };
