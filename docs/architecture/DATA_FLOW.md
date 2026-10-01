# FleetGuard AI --- DATA FLOW

## 1. Purpose

This document defines how vehicle data moves through FleetGuard AI from
generation to user-facing intelligence.

The central pipeline is:

``` text
Vehicle Simulator
 -> MQTT
 -> Kafka
 -> Flink
 -> Redis / MongoDB / PostgreSQL / Object Storage
 -> ML / Analytics
 -> FastAPI
 -> Next.js
 -> AI Fleet Copilot
```

------------------------------------------------------------------------

## 2. End-to-End Flow

``` text
+--------------------+
| Vehicle Simulator  |
+---------+----------+
          |
          | MQTT
          v
+--------------------+
|       EMQX         |
+---------+----------+
          |
          v
+--------------------+
|       Kafka        |
| Durable Event Log  |
+---------+----------+
          |
          v
+--------------------+
|       Flink        |
| Validate           |
| Normalize          |
| Deduplicate        |
| Watermark          |
| Window             |
| Feature generation |
+---+--------+-------+
    |        |
    |        +----------------------+
    |                               |
    v                               v
+---------+                    +-----------+
|  Redis  |                    |  MongoDB  |
| Hot     |                    | Operational|
| State   |                    | State      |
+----+----+                    +-----+-----+
     |                               |
     +---------------+---------------+
                     |
                     v
              +-------------+
              | PostgreSQL  |
              | ACID Core   |
              +------+------+
                     |
                     v
                 FastAPI
                     |
          +----------+----------+
          |                     |
          v                     v
      Next.js               AI Copilot
                                |
                         +------+------+
                         |             |
                         v             v
                      Fleet Data    pgvector
                         Tools        RAG
```

Historical path:

``` text
Kafka
  |
  v
Object Storage
  |
  +--> Raw Parquet
  +--> Clean Parquet
  +--> Curated Parquet
          |
          v
     Batch Analytics
          |
          v
       ML Training
```

------------------------------------------------------------------------

## 3. Vehicle Event Contract

Canonical event:

``` json
{
  "event_id": "evt_123",
  "schema_version": 1,
  "tenant_id": "tenant_01",
  "fleet_id": "fleet_01",
  "vehicle_id": "veh_000042",
  "vin": "SIM00000000042",
  "event_ts": "2026-09-29T12:10:03.120Z",
  "ingest_ts": "2026-09-29T12:10:03.150Z",
  "sequence_no": 88412,
  "event_type": "HARSH_BRAKE",
  "latitude": 13.0827,
  "longitude": 80.2707,
  "speed_kmh": 64.2,
  "acceleration_mps2": -4.1,
  "soc_pct": 41,
  "fuel_pct": null,
  "odometer_km": 18234.7,
  "dtc_codes": ["P0301"],
  "source": "simulator"
}
```

The event identity fields are essential for ordering, deduplication,
tracing, and idempotency.

------------------------------------------------------------------------

## 4. MQTT Data Flow

Topic pattern:

``` text
fleet/{fleet_id}/vehicle/{vehicle_id}/telemetry
fleet/{fleet_id}/vehicle/{vehicle_id}/diagnostics
fleet/{fleet_id}/vehicle/{vehicle_id}/status
```

Example:

``` text
fleet/fleet-001/vehicle/veh-000042/telemetry
```

MQTT is the edge-facing transport.

The vehicle simulator should intentionally generate:

-   duplicate messages
-   delayed messages
-   out-of-order messages
-   network reconnection
-   burst traffic

------------------------------------------------------------------------

## 5. MQTT -\> Kafka

The ingestion layer:

1.  authenticates the MQTT client
2.  validates the envelope
3.  validates the schema
4.  adds ingestion timestamp
5.  converts to canonical format
6.  publishes to Kafka
7.  acknowledges MQTT delivery only after the message has safely entered
    the ingestion pipeline according to the selected delivery semantics

Invalid events go to:

``` text
telemetry.invalid
```

Valid events go to:

``` text
telemetry.raw
```

------------------------------------------------------------------------

## 6. Kafka Topics

Core topics:

``` text
telemetry.raw
telemetry.normalized
telemetry.invalid
telemetry.deduplicated

vehicle.state
vehicle.anomaly
vehicle.alert

driver.events
driver.scores

maintenance.features
maintenance.predictions

fleet.metrics

audit.events

dlq.events
```

Avoid creating excessive topic fragmentation.

------------------------------------------------------------------------

## 7. Kafka Partitioning

Primary key:

``` text
vehicle_id
```

Reason:

``` text
same vehicle
 -> same partition
 -> natural per-vehicle ordering
```

Different vehicles process concurrently.

The exact production partition count must be established through load
testing; it should not be presented as a guaranteed throughput number.

------------------------------------------------------------------------

## 8. Duplicate Event Flow

Duplicate identity:

``` text
event_id
```

Secondary ordering identity:

``` text
vehicle_id + sequence_no
```

Flow:

``` text
Kafka
 |
 v
Flink
 |
 +--> recent event-ID state
 |
 +--> duplicate?
       |
       +--> YES -> discard / metrics / optional audit
       |
       +--> NO  -> continue
```

For high-rate approximate filtering, a Bloom filter may be used as a
first-pass optimization, followed by authoritative state where
necessary.

------------------------------------------------------------------------

## 9. Out-of-Order Flow

Every event carries:

``` text
event_ts
ingest_ts
sequence_no
```

Flink processes using event time.

Example:

``` text
10:00:01 arrives
10:00:03 arrives
10:00:02 arrives late
```

Watermarks determine when a window is considered complete.

``` text
Event stream
 |  |     |
 01 03    02
          ^
          late

Watermark
 ---------->
```

Events beyond the allowed lateness threshold go to a late-event path.

------------------------------------------------------------------------

## 10. Stream Processing

Flink pipeline:

``` text
Kafka
  |
  v
Deserialize
  |
  v
Schema Validation
  |
  v
Normalization
  |
  v
Deduplication
  |
  v
Event-Time Assignment
  |
  v
Watermarks
  |
  v
Window Aggregation
  |
  +--> vehicle state
  +--> anomaly detection
  +--> risk features
  +--> driver features
  +--> maintenance features
  +--> fleet metrics
```

------------------------------------------------------------------------

## 11. Real-Time Risk Flow

Example:

``` text
Telemetry
 |
 +--> speed
 +--> acceleration
 +--> DTC
 +--> temperature
 +--> battery
 |
 v
Flink
 |
 v
Rule engine
 |
 +--> harsh braking
 +--> overspeed
 +--> overheating
 +--> battery anomaly
 |
 v
Risk feature vector
 |
 v
ML service
 |
 v
Risk score
 |
 +--> Kafka
 +--> Redis
 +--> MongoDB
 +--> PostgreSQL alert
 |
 v
FastAPI
 |
 v
Next.js
```

Critical alerts should be generated through the low-latency path rather
than waiting for batch analytics.

------------------------------------------------------------------------

## 12. Predictive Maintenance Flow

``` text
Telemetry
   |
   v
Flink
   |
   v
Maintenance features
   |
   +--> DTC frequency
   +--> engine temperature
   +--> battery health
   +--> mileage
   +--> vehicle age
   +--> historical faults
   +--> maintenance history
   |
   v
ML service
   |
   v
Failure probability
   |
   v
maintenance.predictions
   |
   +--> PostgreSQL
   +--> MongoDB snapshot
   +--> Redis cache
   |
   v
FastAPI
   |
   v
Maintenance dashboard
```

Prediction output must contain a model version.

------------------------------------------------------------------------

## 13. Driver Safety Flow

``` text
Vehicle events
 |
 v
Driver-event association
 |
 v
Feature aggregation
 |
 +--> harsh brakes
 +--> harsh acceleration
 +--> overspeed
 +--> rapid turns
 +--> idle time
 +--> night driving
 |
 v
Driver score engine
 |
 v
driver.scores
 |
 +--> PostgreSQL
 +--> Redis
 +--> historical Parquet
 |
 v
Dashboard / Copilot
```

The score formula should be versioned so historical scores remain
explainable.

------------------------------------------------------------------------

## 14. Cost and Utilization Flow

Historical data is preferred for large-scale analytics.

``` text
Kafka
 |
 v
Object Storage
 |
 v
Parquet
 |
 v
Batch analytics
 |
 +--> utilization
 +--> idle hours
 +--> distance
 +--> fuel/energy
 +--> cost/km
 +--> downtime
 |
 v
Curated datasets
 |
 v
FastAPI analytics endpoints
 |
 v
Next.js
```

Maintenance costs and business records are joined from PostgreSQL.

------------------------------------------------------------------------

## 15. Database Routing

### PostgreSQL

``` text
Fleet
Vehicle
Driver
User
Role
Trip
Maintenance
Alert
Subscription
Audit
Agent action
```

### MongoDB

``` text
Current vehicle state
Recent diagnostics
Anomalies
Prediction snapshots
Operational documents
```

### Redis

``` text
Latest state
Latest risk
Latest driver score
Dashboard counters
Rate limits
Short-lived dedup keys
```

### Parquet

``` text
Raw telemetry
Historical telemetry
Aggregated telemetry
ML features
Historical scores
Training datasets
```

### pgvector

``` text
Maintenance knowledge
DTC knowledge
Fleet policies
Manuals
Procedures
Resolved cases
```

------------------------------------------------------------------------

## 16. Parquet Data Flow

Three logical layers:

``` text
Raw
 |
 v
Clean
 |
 v
Curated
```

### Raw

Closest durable representation of accepted incoming telemetry.

### Clean

Canonical normalized schema.

### Curated

Analytics-specific datasets.

Recommended path:

``` text
s3://fleetguard/
  raw/
    event_date=YYYY-MM-DD/
    hour=HH/

  clean/
    event_date=YYYY-MM-DD/
    fleet_id=...

  curated/
    vehicle_health/
    driver_scores/
    maintenance_features/
    fleet_utilization/
```

Avoid partitioning directly by vehicle at first because 100K vehicles
can cause excessive small files.

------------------------------------------------------------------------

## 17. Batch ML Flow

``` text
Parquet
 |
 v
Feature extraction
 |
 v
Training dataset
 |
 v
Train model
 |
 v
Evaluate against baseline
 |
 v
Model artifact
 |
 v
Model registry
 |
 v
ML inference service
```

Every prediction should carry:

``` text
model_name
model_version
feature_version
prediction_ts
```

------------------------------------------------------------------------

## 18. FastAPI Data Flow

Example vehicle request:

``` text
GET /api/v1/vehicles/{vehicle_id}
```

FastAPI:

``` text
1. validate JWT
2. identify tenant
3. check RBAC
4. query Redis
5. fall back to MongoDB/PostgreSQL if needed
6. return normalized API DTO
```

The frontend does not know database implementation details.

------------------------------------------------------------------------

## 19. Real-Time Dashboard Flow

``` text
Flink
 |
 v
vehicle.state
 |
 v
State service
 |
 v
Redis
 |
 v
FastAPI
 |
 v
SSE / WebSocket
 |
 v
Next.js
```

This avoids browser connections directly to Kafka.

------------------------------------------------------------------------

## 20. AI Copilot Flow

User:

``` text
"Why is vehicle 482 at high risk?"
```

Flow:

``` text
Next.js
 |
 v
FastAPI
 |
 v
Agent
 |
 +--> get_vehicle_state(482)
 +--> get_vehicle_health(482)
 +--> get_active_alerts(482)
 +--> get_maintenance_history(482)
 |
 +--> search_maintenance_knowledge(...)
 |
 v
LLM
 |
 v
Evidence-based response
 |
 v
Next.js
```

The agent should distinguish:

-   live fleet facts
-   historical facts
-   retrieved documentation
-   model predictions
-   recommendations

------------------------------------------------------------------------

## 21. AI Write Action Flow

Example:

``` text
"Create a maintenance work order for vehicle 482."
```

Flow:

``` text
User
 |
 v
Agent proposes action
 |
 v
User confirmation
 |
 v
FastAPI authorization
 |
 v
PostgreSQL transaction
 |
 v
Audit event
 |
 v
Response
```

The LLM never writes directly to PostgreSQL.

------------------------------------------------------------------------

## 22. Backpressure Flow

If Flink slows:

``` text
Vehicles
 -> MQTT
 -> Kafka
 -> backlog/consumer lag
```

Kafka buffers the workload.

When capacity is restored:

``` text
Flink
 -> catches up
 -> lag decreases
```

This is preferable to silently dropping telemetry.

------------------------------------------------------------------------

## 23. Failure Flows

### Kafka failure

``` text
Producer retry
 +
Kafka replication
 +
consumer offset recovery
```

### Flink failure

``` text
checkpoint
 ->
restart
 ->
restore state
 ->
resume
```

### Redis failure

``` text
Redis unavailable
 ->
fallback to durable store
 ->
rebuild cache
```

### PostgreSQL failure

``` text
business writes unavailable
but
telemetry ingestion continues
```

### Object storage failure

``` text
Kafka retains events
 ->
storage writer retries
 ->
historical data catches up
```

------------------------------------------------------------------------

## 24. Trace Correlation

Every event should carry or map to:

``` text
event_id
vehicle_id
trace_id
```

Trace:

``` text
MQTT
 -> Kafka
 -> Flink
 -> ML
 -> FastAPI
 -> Next.js
```

This enables end-to-end latency analysis.

------------------------------------------------------------------------

## 25. Target Latency Paths

### Dashboard

``` text
event
 -> MQTT
 -> Kafka
 -> Flink
 -> Redis
 -> FastAPI
 -> UI
```

Target: under 2 seconds.

### Critical alert

``` text
event
 -> MQTT
 -> Kafka
 -> Flink
 -> risk engine
 -> alert
```

Target: under 5 seconds.

### API

Target:

``` text
p95 <200ms
p99 <500ms
```

These remain test targets rather than claims.

------------------------------------------------------------------------

## 26. Data Lifecycle

``` text
Seconds/minutes
    |
    v
Redis
HOT

Hours/days/weeks
    |
    v
MongoDB/PostgreSQL
WARM

Months/years
    |
    v
Parquet/object storage
COLD
```

Retention must be configurable and support erasure workflows where
applicable.
