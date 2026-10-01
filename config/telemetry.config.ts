export const telemetryConfig = {
  ingestHertz: 0.2,
  batchSize: 500,
  topics: { raw: "vehicle.telemetry.raw", enriched: "vehicle.telemetry.enriched" },
};
