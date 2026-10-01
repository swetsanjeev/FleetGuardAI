import React, { useEffect, useRef } from "react";
import { VehicleLocation } from "../types/telemetry";

export function FleetMap({ locations }: { locations: VehicleLocation[] }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    // TODO: mount Leaflet/Mapbox instance and render markers
  }, [locations]);
  return <div ref={ref} className="fleet-map" data-count={locations.length} />;
}
