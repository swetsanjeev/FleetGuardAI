import { useEffect, useState } from "react";
import { TelemetryPoint } from "../types/telemetry";
import { telemetryService } from "../services/telemetryService";

export function useTelemetry(vin: string) {
  const [points, setPoints] = useState<TelemetryPoint[]>([]);
  useEffect(() => { telemetryService.latest(vin).then(setPoints).catch(() => setPoints([])); }, [vin]);
  return { points };
}
