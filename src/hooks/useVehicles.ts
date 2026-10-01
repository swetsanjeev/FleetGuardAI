import { useEffect, useState } from "react";
import { Vehicle } from "../types/vehicle";
import { vehicleService } from "../services/vehicleService";

export function useVehicles() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  useEffect(() => { vehicleService.list().then(setVehicles).catch(() => setVehicles([])); }, []);
  return { vehicles };
}
