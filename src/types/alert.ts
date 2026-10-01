export type AlertSeverity = "critical" | "warning" | "info";

export interface Alert {
  id: string;
  vehicleVin: string;
  severity: AlertSeverity;
  message: string;
  createdAt: string;
  acknowledged: boolean;
}
