import React from "react";
import { TelemetryPoint } from "../types/telemetry";

export function TelemetryChart({ points }: { points: TelemetryPoint[] }) {
  const latest = points[points.length - 1];
  return (
    <div className="telemetry-chart">
      <span>Speed: {latest?.speedKph ?? 0} km/h</span>
      <span>SOC: {latest?.batterySoc ?? 0}%</span>
    </div>
  );
}
