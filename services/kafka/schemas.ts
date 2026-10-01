export interface TelemetryEventSchema {
  vin: string;
  timestamp: string;
  speedKph: number;
  batterySoc: number;
  lat: number;
  lon: number;
}

export interface DtcEventSchema { vin: string; code: string; severity: string; timestamp: string }
