export interface MaintenanceRecord {
  id: string;
  vehicleVin: string;
  component: string;
  predictedFailureAt: string;
  confidence: number;
  status: "open" | "scheduled" | "completed";
}
