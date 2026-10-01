import React from "react";

export function StatCard({ label, value, delta }: { label: string; value: string; delta?: string }) {
  return (
    <div className="stat-card">
      <span className="label">{label}</span>
      <strong>{value}</strong>
      {delta && <em>{delta}</em>}
    </div>
  );
}
