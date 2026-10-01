import React from "react";
import { PageHeader } from "../components/PageHeader";
import { FleetMap } from "../components/FleetMap";
import { AlertFeed } from "../components/AlertFeed";
import { useAlerts } from "../hooks/useAlerts";

export default function DashboardPage() {
  const { alerts } = useAlerts();
  return (
    <section>
      <PageHeader title="Fleet Dashboard" subtitle="Live connected-vehicle overview" />
      <FleetMap locations={[]} />
      <AlertFeed alerts={alerts} />
    </section>
  );
}
