# FleetGuard AI Architecture

Connected-vehicle platform: telemetry from fleet vehicles flows through Kafka, is
enriched by stream processing, and lands in MongoDB (raw telemetry), PostgreSQL
(business entities), Redis (latest state), and S3/Parquet (analytics). A pgvector
knowledge base powers the AI Fleet Copilot.

## Components

- **Ingestion service** - MQTT/HTTPS gateway for vehicle telemetry
- **Stream processor** - Flink jobs for risk scoring and enrichment
- **API service** - FastAPI business endpoints
- **ML service** - predictive maintenance models
- **AI agent** - copilot orchestration with retrieval over pgvector
