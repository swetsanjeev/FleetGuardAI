import { useEffect, useState } from "react";
import { analyticsService } from "../services/analyticsService";

export function useFleetAnalytics() {
  const [kpis, setKpis] = useState<Record<string, number>>({});
  useEffect(() => { analyticsService.kpis().then(setKpis).catch(() => setKpis({})); }, []);
  return { kpis };
}
