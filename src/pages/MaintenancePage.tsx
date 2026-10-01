import React from "react";
import { useMaintenance } from "../hooks/useMaintenance";

export default function MaintenancePage() {
  const { workOrders } = useMaintenance();
  return <section><h1>Predictive Maintenance</h1><p>{workOrders.length} open work orders</p></section>;
}
