export const formatters = {
  energy: (v: number) => `${v.toFixed(1)} kWh`,
  distance: (v: number) => `${v.toFixed(1)} km`,
  percent: (v: number) => `${Math.round(v)}%`,
};
