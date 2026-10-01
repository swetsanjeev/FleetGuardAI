export interface Trip {
  id: string;
  vehicleVin: string;
  driverId: string;
  startedAt: string;
  endedAt: string;
  distanceKm: number;
  energyUsedKwh: number;
}
