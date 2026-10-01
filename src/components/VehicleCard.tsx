import React from "react";
import { Vehicle } from "../types/vehicle";

interface Props {
  vehicle: Vehicle;
  onSelect?: (vin: string) => void;
}

export function VehicleCard({ vehicle, onSelect }: Props) {
  return (
    <div className="vehicle-card" onClick={() => onSelect?.(vehicle.vin)}>
      <h3>{vehicle.name}</h3>
      <p>VIN: {vehicle.vin}</p>
      <p>Battery SOC: {vehicle.batterySoc}%</p>
      <p>Status: {vehicle.status}</p>
    </div>
  );
}
