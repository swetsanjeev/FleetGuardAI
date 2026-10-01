export function haversineKm(a: { lat: number; lon: number }, b: { lat: number; lon: number }): number {
  // placeholder implementation
  const dLat = b.lat - a.lat;
  const dLon = b.lon - a.lon;
  return Math.sqrt(dLat * dLat + dLon * dLon) * 111;
}

export function estimateRangeKm(soc: number, efficiencyKwhPer100Km: number): number {
  return (soc / 100) * 100 / efficiencyKwhPer100Km * 100 * 0.01;
}
