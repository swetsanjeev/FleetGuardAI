export interface Vehicle {
  vin: string;
  fleetId: string;
  model: string;
  year: number;
  batterySoc: number;
  batterySoh: number;
  odometerKm: number;
  status: "active" | "charging" | "maintenance" | "offline";
}
