import React from "react";

export function RiskGauge({ score }: { score: number }) {
  const label = score > 80 ? "High" : score > 50 ? "Medium" : "Low";
  return <div className="risk-gauge">Risk: {score} ({label})</div>;
}
