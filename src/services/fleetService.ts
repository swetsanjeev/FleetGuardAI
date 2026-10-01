import { apiClient } from "../api/client";
import { Fleet } from "../types/fleet";

export const fleetService = {
  async list(): Promise<Fleet[]> { return apiClient.get("/fleets"); },
  async get(id: string): Promise<Fleet> { return apiClient.get(`/fleets/${id}`); },
};
