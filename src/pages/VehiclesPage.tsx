import React from "react";
import { VehicleCard } from "../components/VehicleCard";
import { useVehicles } from "../hooks/useVehicles";

export default function VehiclesPage() {
  const { vehicles } = useVehicles();
  return <section>{vehicles.map((v) => <VehicleCard key={v.vin} vehicle={v} />)}</section>;
}
