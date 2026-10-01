# Database Design

- **PostgreSQL**: organizations, fleets, vehicles, drivers, trips, alerts, maintenance, risk.
- **MongoDB**: telemetry documents and DTC events (`telemetry_events`, `dtc_events`).
- **Redis**: latest vehicle state cache and rate limiting.
- **S3 + Parquet**: analytics exports partitioned by date.
- **pgvector**: embeddings for copilot retrieval.
