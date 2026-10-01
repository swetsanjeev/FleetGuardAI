export type VehicleStatus = "active" | "charging" | "maintenance" | "offline";

export interface Vehicle {
  vin: string;
  name: string;
  model: string;
  year: number;
  fleetId: string;
  status: VehicleStatus;
  batterySoc: number;
  batterySoh: number;
  odometerKm: number;
}
