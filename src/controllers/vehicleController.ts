import { vehicleService } from "../services/vehicleService";

export async function listVehicles() { return vehicleService.list(); }
export async function getVehicle(vin: string) { return vehicleService.get(vin); }
