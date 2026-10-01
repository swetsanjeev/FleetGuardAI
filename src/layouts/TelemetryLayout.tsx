import React from "react";

export function TelemetryLayout({ children }: { children: React.ReactNode }) {
  return <div className="telemetry-layout"><header>Live Telemetry</header>{children}</div>;
}
