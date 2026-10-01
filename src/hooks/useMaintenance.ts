import { useEffect, useState } from "react";
import { maintenanceService } from "../services/maintenanceService";

export function useMaintenance() {
  const [workOrders, setWorkOrders] = useState<any[]>([]);
  useEffect(() => { maintenanceService.workOrders().then(setWorkOrders).catch(() => setWorkOrders([])); }, []);
  return { workOrders };
}
