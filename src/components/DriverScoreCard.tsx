import React from "react";
import { Driver } from "../types/driver";

export function DriverScoreCard({ driver }: { driver: Driver }) {
  return (
    <div className="driver-score-card">
      <h4>{driver.fullName}</h4>
      <p>Safety score: {driver.safetyScore}</p>
      <p>Trips: {driver.tripCount}</p>
    </div>
  );
}
