import React from "react";
import { Alert } from "../types/alert";
import { AlertBadge } from "./AlertBadge";

export function AlertFeed({ alerts }: { alerts: Alert[] }) {
  return (
    <ul className="alert-feed">
      {alerts.map((a) => (
        <li key={a.id}><AlertBadge severity={a.severity} /> {a.message}</li>
      ))}
    </ul>
  );
}
