import React from "react";

export function BatteryGauge({ soc, soh }: { soc: number; soh: number }) {
  return (
    <div className="battery-gauge">
      <div>State of Charge: {soc}%</div>
      <div>State of Health: {soh}%</div>
    </div>
  );
}
