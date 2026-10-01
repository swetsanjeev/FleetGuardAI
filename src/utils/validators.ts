export function isValidVin(vin: string) { return /^[A-HJ-NPR-Z0-9]{17}$/i.test(vin); }
export function isValidSoc(soc: number) { return soc >= 0 && soc <= 100; }
