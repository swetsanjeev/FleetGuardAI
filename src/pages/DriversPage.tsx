import React from "react";
import { useDriverScore } from "../hooks/useDriverScore";
import { DriverScoreCard } from "../components/DriverScoreCard";

export default function DriversPage() {
  const { drivers } = useDriverScore();
  return <section>{drivers.map((d) => <DriverScoreCard key={d.id} driver={d} />)}</section>;
}
