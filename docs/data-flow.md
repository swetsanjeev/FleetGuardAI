# Data Flow

1. Vehicle ECU publishes DTC and battery metrics over MQTT.
2. Ingestion validates and publishes to `vehicle.telemetry.raw`.
3. Flink enriches with vehicle metadata -> `vehicle.telemetry.enriched`.
4. PostgreSQL stores trips/alerts; MongoDB stores telemetry documents; Redis caches latest state.
5. Nightly batch writes Parquet partitions to S3 for fleet analytics.
