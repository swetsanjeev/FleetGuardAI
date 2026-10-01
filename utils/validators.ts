export function isValidVin(vin: string): boolean {
  return /^[A-HJ-NPR-Z0-9]{17}$/i.test(vin);
}
export function clampSoc(value: number): number {
  return Math.min(100, Math.max(0, value));
}
