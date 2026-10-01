export function weightRiskFactor(factor: string): number {
  const weights: Record<string, number> = { harsh_braking: 12, rapid_acceleration: 9, speeding: 15, battery_temp_spikes: 18 };
  return weights[factor] ?? 3;
}
export function aggregateRisk(factors: string[]): number {
  return Math.min(100, factors.reduce((s, f) => s + weightRiskFactor(f), 0));
}
