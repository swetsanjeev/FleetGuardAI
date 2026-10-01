import { telemetryService } from "../services/telemetryService";

export async function latestTelemetry(vin: string) { return telemetryService.latest(vin); }
