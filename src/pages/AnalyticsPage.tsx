import React from "react";
import { useFleetAnalytics } from "../hooks/useFleetAnalytics";

export default function AnalyticsPage() {
  const { kpis } = useFleetAnalytics();
  return <section><h1>Fleet Analytics</h1><pre>{JSON.stringify(kpis, null, 2)}</pre></section>;
}
