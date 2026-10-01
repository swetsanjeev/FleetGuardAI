import { apiClient } from "./client";
import { VehicleDto } from "../dtos/VehicleDto";

export const vehiclesApi = {
  list: () => apiClient.get("/vehicles") as Promise<VehicleDto[]>,
  detail: (vin: string) => apiClient.get(`/vehicles/${vin}`) as Promise<VehicleDto>,
};
