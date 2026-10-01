import { useEffect, useState } from "react";
import { Alert } from "../types/alert";
import { alertService } from "../services/alertService";

export function useAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  useEffect(() => { alertService.list().then(setAlerts).catch(() => setAlerts([])); }, []);
  return { alerts };
}
