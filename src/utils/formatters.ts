export function formatKwh(v: number) { return `${v.toFixed(1)} kWh`; }
export function formatKm(v: number) { return `${v.toLocaleString()} km`; }
export function formatDate(iso: string) { return new Date(iso).toLocaleString(); }
