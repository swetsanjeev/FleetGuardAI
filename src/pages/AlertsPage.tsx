import React from "react";
import { AlertFeed } from "../components/AlertFeed";
import { useAlerts } from "../hooks/useAlerts";

export default function AlertsPage() {
  const { alerts } = useAlerts();
  return <section><h1>Alerts</h1><AlertFeed alerts={alerts} /></section>;
}
