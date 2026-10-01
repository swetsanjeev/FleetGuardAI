export interface TelemetryPoint {
  timestamp: string;
  speedKph: number;
  batterySoc: number;
  batterySoh: number;
  lat: number;
  lon: number;
  odometerKm: number;
}

export interface VehicleLocation { vin: string; lat: number; lon: number }

export interface DtcCode { code: string; description: string; severity: string }
