import React from "react";
import { AlertSeverity } from "../types/alert";

const COLORS: Record<AlertSeverity, string> = { critical: "#d32f2f", warning: "#f9a825", info: "#1976d2" };

export function AlertBadge({ severity }: { severity: AlertSeverity }) {
  return <span className="alert-badge" style={{ background: COLORS[severity] }}>{severity}</span>;
}
