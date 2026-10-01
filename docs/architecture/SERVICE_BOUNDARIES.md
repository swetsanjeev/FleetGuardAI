# FleetGuard AI --- SERVICE BOUNDARIES

## 1. Purpose

This document defines ownership boundaries between FleetGuard AI
services, databases, APIs, ML components, and AI-agent tools.

The key rule is:

> A component should own a responsibility and expose an explicit
> contract rather than allowing arbitrary cross-component database
> access.

------------------------------------------------------------------------

# 2. Logical Service Map

``` text
+------------------+
| Vehicle Simulator|
+--------+---------+
         |
         v
+------------------+
| MQTT Ingestion   |
+--------+---------+
         |
         v
+------------------+
| Kafka Backbone   |
+--------+---------+
         |
         v
+------------------+
| Stream Processor |
|      Flink       |
+--+----+----+-----+
   |    |    |
   |    |    +------------------+
   |    |                       |
   v    v                       v
Redis MongoDB              ML Service
   |    |                       |
   +----+-----------+-----------+
                    |
                    v
              PostgreSQL
                    |
                    v
                FastAPI
             /           \
            v             v
        Next.js       Copilot
                         |
                   +-----+------+
                   |            |
                   v            v
                Tools       pgvector
```

------------------------------------------------------------------------

# 3. Service Boundary Principles

## Principle 1 --- Own your data

A service may read another service's data only through an explicit
contract unless it is an approved analytical read path.

## Principle 2 --- No arbitrary shared database access

The frontend and LLM never directly access databases.

## Principle 3 --- Events for high-volume state propagation

Kafka is used for asynchronous high-volume data movement.

## Principle 4 --- APIs for business operations

FastAPI is the controlled application boundary for user-facing business
operations.

## Principle 5 --- Database ownership must be explicit

Each database/table/collection has an owning service.

## Principle 6 --- Read models may be denormalized

Redis and MongoDB can contain projections of PostgreSQL/event data.

------------------------------------------------------------------------

# 4. Vehicle Simulator Service

## Responsibility

Generate synthetic vehicle telemetry at scale.

## Owns

-   vehicle simulation state
-   fault injection
-   trip simulation
-   event generation scenarios

## Reads

-   simulation configuration
-   seed data
-   scenario definitions

## Produces

MQTT messages.

## Does not

-   write PostgreSQL
-   write MongoDB
-   call ML directly
-   bypass MQTT/Kafka

## Contract

``` text
publishTelemetry(event)
```

------------------------------------------------------------------------

# 5. MQTT Ingestion Service

## Responsibility

Bridge the vehicle/IoT boundary into the event backbone.

## Reads

MQTT messages.

## Produces

Kafka events.

## Owns

-   MQTT authentication
-   schema validation at ingress
-   canonical event envelope
-   ingestion timestamp
-   malformed-event handling

## Does not

-   perform complex analytics
-   query PostgreSQL per event
-   call the LLM

## Failure behavior

Retry Kafka publishing and expose ingestion health metrics.

------------------------------------------------------------------------

# 6. Kafka Boundary

Kafka is infrastructure rather than a conventional business
microservice.

## Owns

Durable event transport.

## Provides

-   partitioning
-   replay
-   consumer groups
-   buffering
-   ordering within partition
-   event retention

## Producers

-   MQTT ingestion
-   Flink
-   audit service
-   ML service where appropriate

## Consumers

-   Flink
-   data-lake writer
-   analytics consumers
-   alert consumers
-   audit pipelines

------------------------------------------------------------------------

# 7. Stream Processing Service

## Technology

Apache Flink.

## Responsibility

High-volume event processing.

## Owns

-   normalization
-   deduplication
-   event-time processing
-   watermarks
-   windows
-   streaming feature computation
-   real-time anomaly rules
-   state projections

## Reads

``` text
telemetry.raw
```

## Produces

``` text
telemetry.normalized
telemetry.deduplicated
vehicle.state
vehicle.anomaly
vehicle.alert
driver.events
maintenance.features
fleet.metrics
```

## Does not

-   perform user authentication
-   serve frontend requests
-   perform arbitrary transactional writes

------------------------------------------------------------------------

# 8. Vehicle State Service

## Responsibility

Maintain the operational representation of the latest vehicle state.

## Reads

``` text
vehicle.state
```

## Writes

``` text
Redis
MongoDB
```

## Owns

-   latest state projection
-   latest location
-   operational state document

## API

Internal:

``` text
getVehicleState(vehicle_id)
```

## Failure

Rebuild projections from Kafka/MongoDB.

------------------------------------------------------------------------

# 9. Alert Service

## Responsibility

Manage real-time vehicle/fleet alerts.

## Reads

``` text
vehicle.anomaly
vehicle.alert
```

## Writes

PostgreSQL:

``` text
alerts
alert_acknowledgements
```

Redis:

``` text
fleet:{fleet_id}:alerts
vehicle:{vehicle_id}:risk
```

## Owns

-   alert lifecycle
-   severity
-   acknowledgement
-   escalation metadata

## API

Internal:

``` text
createAlert()
acknowledgeAlert()
getActiveAlerts()
```

------------------------------------------------------------------------

# 10. Maintenance Service

## Responsibility

Manage predictive maintenance workflows.

## Reads

``` text
maintenance.predictions
vehicle health
maintenance history
```

## Writes

PostgreSQL:

``` text
maintenance_plans
maintenance_work_orders
maintenance_records
```

MongoDB may store operational prediction snapshots.

## Owns

-   work orders
-   maintenance status
-   maintenance recommendations
-   maintenance workflow

## API

``` text
getMaintenanceHistory(vehicle_id)
getMaintenanceRecommendations(vehicle_id)
createWorkOrder(vehicle_id, ...)
updateWorkOrder(...)
```

------------------------------------------------------------------------

# 11. ML Service

## Responsibility

Model inference.

## Owns

-   model loading
-   model versioning metadata
-   inference
-   feature schema compatibility
-   prediction output

## Reads

Feature vectors.

## Produces

``` text
maintenance.predictions
risk predictions
driver scores
```

## Interface

``` text
POST /internal/v1/predict/maintenance
POST /internal/v1/predict/risk
POST /internal/v1/predict/driver-score
```

Example:

``` json
{
  "vehicle_id": "veh-42",
  "features": {
    "dtc_count_24h": 4,
    "harsh_brakes_1h": 3,
    "temperature_mean": 91.2
  },
  "model_version": "maintenance-v1"
}
```

Response:

``` json
{
  "vehicle_id": "veh-42",
  "probability": 0.81,
  "prediction_horizon_days": 7,
  "model_version": "maintenance-v1"
}
```

## Failure

Inference failure must not stop ingestion. Critical deterministic rules
can continue independently.

------------------------------------------------------------------------

# 12. Analytics Service

## Responsibility

Historical fleet analytics.

## Reads

Primarily:

``` text
Parquet
PostgreSQL business data
```

## Produces

-   utilization metrics
-   cost metrics
-   fleet trends
-   historical summaries

## Does not

Run high-frequency per-event database writes.

------------------------------------------------------------------------

# 13. Data Lake Writer

## Responsibility

Persist historical telemetry into object storage.

## Reads

Kafka.

## Writes

Parquet.

## Owns

-   raw/clean/curated dataset generation
-   batching
-   file rotation
-   compaction
-   partitioning

## Partitioning

``` text
event_date
hour
fleet_id where useful
```

Avoid direct vehicle-level partitions initially.

------------------------------------------------------------------------

# 14. PostgreSQL Ownership

PostgreSQL should be logically divided into domains.

## Identity domain

``` text
users
roles
permissions
tenant_memberships
```

## Fleet domain

``` text
tenants
fleets
vehicles
drivers
vehicle_driver_assignments
```

## Trip domain

``` text
trips
```

## Alert domain

``` text
alerts
alert_acknowledgements
```

## Maintenance domain

``` text
maintenance_plans
maintenance_records
maintenance_work_orders
```

## Subscription domain

``` text
subscriptions
```

## Audit domain

``` text
audit_records
agent_actions
```

------------------------------------------------------------------------

# 15. PostgreSQL Service Boundary

Services must not all share arbitrary SQL access.

Preferred:

``` text
FastAPI
 |
 +--> Fleet repository
 +--> Alert repository
 +--> Maintenance repository
 +--> Identity repository
```

Domain repositories own SQL access.

This makes the code easier to test and migrate.

------------------------------------------------------------------------

# 16. MongoDB Boundary

MongoDB is for operational documents.

Collections:

``` text
vehicle_state
recent_events
diagnostic_events
anomaly_events
prediction_snapshots
fleet_activity
```

MongoDB is not the authoritative source for:

-   users
-   permissions
-   billing
-   maintenance work orders
-   subscriptions

Those belong in PostgreSQL.

------------------------------------------------------------------------

# 17. Redis Boundary

Redis is ephemeral.

Key patterns:

``` text
vehicle:{vehicle_id}:state
vehicle:{vehicle_id}:risk
vehicle:{vehicle_id}:location

driver:{driver_id}:score

fleet:{fleet_id}:summary
fleet:{fleet_id}:alerts

dedup:event:{event_id}

ratelimit:{tenant_id}:{endpoint}
```

Rules:

1.  Never rely on Redis as the only copy of business truth.
2.  All critical data must be recoverable.
3.  TTLs must be explicit.
4.  Cache invalidation must be owned by the service producing the state.

------------------------------------------------------------------------

# 18. FastAPI Boundary

FastAPI is the primary application boundary.

## Public responsibilities

-   authentication
-   authorization
-   fleet APIs
-   vehicle APIs
-   driver APIs
-   maintenance APIs
-   alert APIs
-   analytics APIs
-   Copilot API

## Internal responsibilities

-   service orchestration
-   DTO conversion
-   rate limiting
-   audit
-   tenant checks

## FastAPI must not

-   run long stream-processing jobs
-   consume raw Kafka telemetry synchronously per API request
-   contain model-training code
-   give LLMs unrestricted database access

------------------------------------------------------------------------

# 19. API Boundary

## Authentication

``` text
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
```

## Fleet

``` text
GET /api/v1/fleets
GET /api/v1/fleets/{fleet_id}
GET /api/v1/fleets/{fleet_id}/summary
```

## Vehicle

``` text
GET /api/v1/vehicles
GET /api/v1/vehicles/{vehicle_id}
GET /api/v1/vehicles/{vehicle_id}/state
GET /api/v1/vehicles/{vehicle_id}/health
GET /api/v1/vehicles/{vehicle_id}/risk
GET /api/v1/vehicles/{vehicle_id}/maintenance
```

## Alerts

``` text
GET /api/v1/alerts
GET /api/v1/alerts/{alert_id}
POST /api/v1/alerts/{alert_id}/acknowledge
```

## Drivers

``` text
GET /api/v1/drivers
GET /api/v1/drivers/{driver_id}/score
```

## Analytics

``` text
GET /api/v1/analytics/utilization
GET /api/v1/analytics/cost
GET /api/v1/analytics/maintenance
```

## Copilot

``` text
POST /api/v1/copilot/chat
POST /api/v1/copilot/actions/{action_id}/approve
```

------------------------------------------------------------------------

# 20. Next.js Boundary

Next.js owns:

-   UI rendering
-   user interaction
-   frontend state
-   charts
-   maps
-   Copilot interface

Next.js does not own:

-   business rules
-   database access
-   authorization decisions
-   ML inference
-   Kafka consumption

------------------------------------------------------------------------

# 21. Real-Time UI Boundary

Recommended:

``` text
Flink
 -> vehicle.state
 -> Redis
 -> FastAPI
 -> SSE/WebSocket
 -> Next.js
```

The browser should not connect to Kafka.

------------------------------------------------------------------------

# 22. AI Copilot Boundary

The Copilot has three logical components:

``` text
Copilot API
Agent Runtime
Knowledge/RAG Layer
```

## Copilot API

Handles:

-   chat sessions
-   authentication context
-   rate limiting
-   audit metadata

## Agent Runtime

Handles:

-   reasoning loop
-   tool selection
-   guardrails
-   response generation

## RAG Layer

Handles:

-   embedding
-   semantic retrieval
-   document filtering
-   context construction

------------------------------------------------------------------------

# 23. AI Tool Boundary

The agent receives only explicit tools.

## Read tools

``` text
get_fleet_summary(fleet_id)

get_vehicle_state(vehicle_id)

get_vehicle_health(vehicle_id)

get_active_alerts(fleet_id)

get_maintenance_history(vehicle_id)

get_driver_safety_score(driver_id, period)

get_fleet_cost_summary(fleet_id, period)

search_maintenance_knowledge(query, filters)
```

## Action tools

Potentially:

``` text
create_maintenance_work_order(...)
acknowledge_alert(...)
```

Action tools require:

``` text
authentication
authorization
validation
user confirmation where required
audit logging
```

------------------------------------------------------------------------

# 24. AI Does Not Get Direct DB Access

Incorrect:

``` text
LLM
 |
 +--> SQL
 +--> Mongo query
 +--> Redis command
```

Correct:

``` text
LLM
 |
 v
Typed Tool
 |
 v
Authorized Service
 |
 v
Database
```

This prevents arbitrary data access and makes agent behavior auditable.

------------------------------------------------------------------------

# 25. pgvector Boundary

pgvector owns semantic knowledge retrieval.

Documents:

``` text
maintenance manuals
DTC explanations
fleet policies
maintenance procedures
vehicle specifications
resolved cases
```

The vector layer does not become a second operational database.

------------------------------------------------------------------------

# 26. Security Boundaries

``` text
Internet
 |
 v
WAF / Load Balancer
 |
 v
FastAPI / Next.js
 |
 v
Application network
 |
 +--> PostgreSQL
 +--> MongoDB
 +--> Redis
 +--> Kafka
 +--> ML
 +--> Copilot
```

Vehicle boundary:

``` text
Vehicle Simulator
 |
 | mTLS/TLS
 v
MQTT
 |
 | TLS
 v
Kafka
```

------------------------------------------------------------------------

# 27. Tenant Boundary

Every user request is associated with:

``` text
tenant_id
```

Authorization:

``` text
User
 |
 v
Role
 |
 v
Tenant
 |
 v
Resource
```

A user must never access another tenant's vehicle, driver, alert, or
analytics data.

Tenant filtering must happen server-side.

------------------------------------------------------------------------

# 28. Audit Boundary

Audit events:

``` text
audit.events
```

Example:

``` json
{
  "actor_id": "user-42",
  "tenant_id": "tenant-01",
  "action": "CREATE_MAINTENANCE_ORDER",
  "resource_id": "vehicle-42",
  "source": "AI_COPILOT",
  "timestamp": "2026-09-29T12:10:03Z",
  "result": "SUCCESS"
}
```

Audit ownership includes:

-   data access
-   authentication/security events
-   administrative actions
-   AI-agent actions
-   maintenance actions

------------------------------------------------------------------------

# 29. Failure Boundaries

## Redis failure

Affected:

-   low-latency reads
-   dashboard freshness

Unaffected:

-   durable business records
-   historical telemetry

## MongoDB failure

Affected:

-   operational document reads

Unaffected:

-   PostgreSQL business truth
-   historical Parquet

## PostgreSQL failure

Affected:

-   transactional business operations

Unaffected:

-   raw telemetry ingestion
-   Kafka buffering

## ML failure

Affected:

-   predictive outputs

Unaffected:

-   deterministic stream processing
-   telemetry ingestion

## Copilot failure

Affected:

-   AI interaction

Unaffected:

-   core fleet monitoring

This means AI is an enhancement, not a system-wide dependency.

------------------------------------------------------------------------

# 30. Scaling Boundaries

  Component          Scaling mechanism
  ------------------ -----------------------------------------------
  Simulator          Worker replicas
  MQTT               Broker cluster
  Kafka              Brokers + partitions
  Flink              Parallelism + task managers
  Redis              Replica/cluster
  MongoDB            Replica set/sharding
  PostgreSQL         Connection pooling/read replicas/partitioning
  ML                 Inference replicas
  FastAPI            Horizontal replicas
  Next.js            Horizontal replicas
  Copilot            Horizontal replicas
  Data lake writer   Consumer parallelism
  Observability      Horizontal/managed scaling

------------------------------------------------------------------------

# 31. Local Deployment Boundaries

Docker Compose groups the entire development environment.

``` text
simulator
mqtt
kafka
flink
postgres
mongodb
redis
minio
ml
backend
copilot
frontend
observability
```

The local environment should preserve the same logical service
boundaries used in production.

------------------------------------------------------------------------

# 32. Production Deployment Boundaries

Kubernetes deployments:

``` text
fleetguard-frontend
fleetguard-api
fleetguard-copilot
fleetguard-ml
fleetguard-simulator
fleetguard-stream-processing
fleetguard-ingestion
fleetguard-alerts
fleetguard-maintenance
```

Stateful infrastructure is deployed separately or provided by managed
services.

------------------------------------------------------------------------

# 33. Communication Matrix

  --------------------------------------------------------------------------
  From              To                Mechanism            Purpose
  ----------------- ----------------- -------------------- -----------------
  Simulator         MQTT              MQTT                 Vehicle telemetry

  MQTT              Kafka             Producer             Durable ingestion

  Kafka             Flink             Consumer             Stream processing

  Flink             Kafka             Producer             Derived events

  Flink             Redis             Client               Hot state

  Flink             MongoDB           Client/service       Operational
                                                           projections

  Flink             ML                Internal API/Kafka   Inference

  ML                Kafka             Producer             Predictions

  ML                PostgreSQL        Service/repository   Prediction
                                                           records where
                                                           required

  Kafka             Data lake         Consumer             Historical
                                                           storage

  FastAPI           Redis             Client               Low-latency reads

  FastAPI           MongoDB           Client               Operational reads

  FastAPI           PostgreSQL        Repository           Business
                                                           operations

  FastAPI           ML                HTTP                 Inference/query

  Next.js           FastAPI           HTTPS                Application API

  Next.js           FastAPI           SSE/WebSocket        Live updates

  Copilot           Fleet services    Tools/API            Fleet facts

  Copilot           pgvector          Retrieval service    Knowledge

  Copilot           FastAPI           HTTPS/internal API   Controlled
                                                           actions
  --------------------------------------------------------------------------

------------------------------------------------------------------------

# 34. Event vs API Decision

Use **events** when:

-   throughput is high
-   processing is asynchronous
-   multiple consumers need the same data
-   replay is useful
-   the operation does not require immediate user response

Use **APIs** when:

-   a user is requesting information
-   a business operation requires immediate response
-   authorization is required
-   transactional state must change

Example:

``` text
Telemetry -> Kafka event
Create work order -> API
Risk prediction -> event
Acknowledge alert -> API
Historical analytics -> API over analytical data
```

------------------------------------------------------------------------

# 35. Service Deployment Strategy

Do not force every logical service into an independently deployed
microservice immediately.

Initial deployment units can be:

``` text
1. ingestion
2. stream-processing
3. ML
4. backend
5. copilot
6. frontend
```

Logical domain boundaries remain explicit inside these deployments.

Split further only when:

-   independent scaling is required
-   independent failure isolation is required
-   ownership becomes separate
-   deployment cadence requires it

This avoids unnecessary microservice complexity while preserving future
scalability.
