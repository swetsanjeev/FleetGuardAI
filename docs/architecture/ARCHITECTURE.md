# FleetGuard AI --- ARCHITECTURE

## 1. Purpose

FleetGuard AI is a production-oriented connected-vehicle intelligence
platform focused on:

1.  Predictive maintenance
2.  Real-time vehicle anomaly/risk detection
3.  Driver safety scoring
4.  Fleet cost/utilization intelligence
5.  AI Fleet Copilot

This architecture treats the Connected Vehicle Intelligence Hackathon
problem statement as the authoritative requirements source.

The hackathon requires:

-   100,000+ simulated vehicles
-   100,000+ events/sec sustained throughput
-   3x burst handling for 5 minutes without data loss
-   real-time and batch analytics
-   relational + NoSQL + vector storage
-   secure APIs and usable UI
-   containerization
-   Kubernetes
-   Terraform
-   CI/CD
-   observability
-   security
-   automated testing
-   cloud portability

Target NFRs from the problem statement:

  Requirement                              Target
  ------------------------- ---------------------
  Sustained throughput        100,000+ events/sec
  Burst                          3x for 5 minutes
  Dashboard latency                       \<2 sec
  Critical alert latency                  \<5 sec
  API p95                                \<200 ms
  API p99                                \<500 ms
  Availability                              99.9%
  Core unit-test coverage                  \>=80%

These are validation targets, not claimed performance results.

------------------------------------------------------------------------

## 2. Architecture Principles

### 2.1 Depth over breadth

The platform deliberately concentrates on five connected capabilities
rather than adding unrelated features.

### 2.2 Separate data plane from application plane

**Data plane**

Vehicle -\> MQTT -\> Kafka -\> Flink -\> storage/ML

**Application plane**

FastAPI -\> Next.js and AI Copilot -\> controlled data tools

### 2.3 No single database owns everything

Each datastore has one clearly defined responsibility.

### 2.4 Kafka is the durable event backbone

Kafka absorbs bursts, provides replay, decouples producers and
consumers, and supports backpressure.

### 2.5 PostgreSQL is not the raw telemetry store

PostgreSQL stores transactional/business truth. High-volume telemetry
belongs in the event stream and data lake.

### 2.6 At-least-once delivery + idempotency

The architecture does not claim global exactly-once semantics.
Duplicate-safe consumers use event IDs, sequence numbers, and idempotent
writes.

### 2.7 AI is tool-governed

The LLM never receives database credentials or arbitrary database
access. It calls authorized application tools.

### 2.8 Cloud-neutral application design

The application uses portable protocols and infrastructure components.
Terraform provides cloud-specific infrastructure modules.

------------------------------------------------------------------------

## 3. High-Level Architecture

``` text
                         +----------------------+
                         |   Vehicle Simulator  |
                         |    100K+ vehicles    |
                         +----------+-----------+
                                    |
                                  MQTT
                                    |
                                    v
                         +----------------------+
                         |        EMQX          |
                         |     MQTT Broker      |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |        Kafka         |
                         | Durable Event Stream  |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |        Flink         |
                         | Stream Processing    |
                         +----+----+----+-------+
                              |    |    |
                +-------------+    |    +----------------+
                |                  |                     |
                v                  v                     v
          +-----------+      +-----------+        +-------------+
          |   Redis   |      |  MongoDB  |        | Object Store|
          | Hot State |      | Operational|       |   Parquet   |
          +-----+-----+      +-----+-----+        +------+------+
                |                  |                      |
                +------------------+----------------------+
                                   |
                                   v
                           +---------------+
                           | ML / Analytics |
                           +-------+-------+
                                   |
                       +-----------+-----------+
                       |                       |
                       v                       v
                +-------------+         +-------------+
                | PostgreSQL  |         |  pgvector   |
                | ACID Core   |         | RAG Knowledge|
                +------+------+         +------+------+
                       |                       |
                       +-----------+-----------+
                                   |
                                   v
                             +-----------+
                             |  FastAPI  |
                             +-----+-----+
                                   |
                    +--------------+---------------+
                    |                              |
                    v                              v
              +-----------+                  +-----------+
              |  Next.js  |                  | AI Copilot|
              | Fleet UI  |                  | Agent/RAG |
              +-----------+                  +-----------+
```

------------------------------------------------------------------------

## 4. Component Decisions

### 4.1 Vehicle Simulator

**Why it exists**

The simulator is a required part of the solution. It must generate
realistic vehicle telemetry at the required scale.

**Receives**

-   vehicle count
-   event rate
-   fleet configuration
-   vehicle type
-   fault probabilities
-   duplicate probability
-   delay probability
-   out-of-order probability
-   burst configuration

**Produces**

-   location
-   speed
-   acceleration
-   odometer
-   battery/fuel state
-   diagnostics
-   event type
-   event ID
-   sequence number
-   event timestamp

**Technology**

Python with asynchronous/concurrent workers.

**Failure**

The simulator retries MQTT delivery and supports reconnect/replay
scenarios.

**Scaling**

Partition vehicles deterministically across simulator workers.

**Security**

Use simulated credentials/certificates. Never use real vehicle-owner
data.

------------------------------------------------------------------------

### 4.2 MQTT / EMQX

**Why**

MQTT is an IoT-oriented publish/subscribe protocol and is suitable for
the vehicle edge boundary.

**Receives**

Vehicle telemetry messages.

**Produces**

Messages to the ingestion layer.

**Technology**

EMQX.

**Failure**

Connection retries, broker buffering where configured, and downstream
Kafka buffering.

**Scaling**

Broker cluster and connection distribution.

**Security**

mTLS, TLS 1.3, device identity, topic-level authorization.

------------------------------------------------------------------------

### 4.3 Kafka

**Why**

Kafka is the durable event backbone.

**Receives**

Normalized vehicle events.

**Produces**

Replayable streams for Flink, analytics, alerts, data lake ingestion,
and downstream consumers.

**Technology**

Apache Kafka.

**Failure**

Replication, producer retries, consumer offset recovery.

**Scaling**

Partition by vehicle ID. Add partitions/brokers based on load testing.

**Security**

TLS, SASL where appropriate, ACLs, isolated credentials.

------------------------------------------------------------------------

### 4.4 Flink

**Why**

Flink provides event-time processing, stateful processing, watermarks,
windows, late-event handling, and checkpoint-based recovery.

**Receives**

Kafka events.

**Produces**

-   normalized events
-   deduplicated events
-   vehicle state
-   anomaly events
-   alerts
-   feature vectors
-   fleet aggregates
-   ML inference requests

**Failure**

Checkpoint recovery.

**Scaling**

Increase parallelism/task managers.

**Security**

Kafka credentials and service identity stored as secrets.

------------------------------------------------------------------------

### 4.5 PostgreSQL

**Purpose**

ACID business system of record.

**Stores**

-   tenants
-   fleets
-   vehicles
-   drivers
-   users
-   roles
-   assignments
-   trips
-   maintenance plans
-   work orders
-   alerts
-   acknowledgements
-   risk-score records
-   driver-score records
-   subscriptions
-   audit records
-   agent actions

**Does not store**

The complete raw telemetry stream.

**Failure**

Business writes may temporarily fail, but telemetry ingestion remains
decoupled.

**Scaling**

Read replicas, indexes, connection pooling, partitioning for selected
high-volume relational tables, materialized views where justified.

**Security**

Private network, encryption, least-privilege DB roles, encrypted
backups.

------------------------------------------------------------------------

### 4.6 MongoDB

**Purpose**

Operational NoSQL document storage.

**Stores**

-   current/recent vehicle state snapshots
-   recent diagnostic documents
-   anomaly documents
-   prediction snapshots
-   flexible operational records

**Failure**

Operational views may temporarily degrade. Historical data remains in
the data lake.

**Scaling**

Replica sets and sharding where justified by measured workload.

------------------------------------------------------------------------

### 4.7 Redis

**Purpose**

Low-latency ephemeral state and cache.

**Stores**

-   latest vehicle state
-   latest location
-   latest risk score
-   latest driver score
-   dashboard summaries
-   rate-limit counters
-   short-lived deduplication keys

**Does not store**

Authoritative business data.

**Failure**

Fall back to MongoDB/PostgreSQL and rebuild Redis state.

**Scaling**

Redis replication/cluster depending on production load.

------------------------------------------------------------------------

### 4.8 Object Storage / Parquet

**Purpose**

Historical telemetry and batch analytics.

**Local**

MinIO.

**Cloud**

S3-compatible object storage such as AWS S3, GCS, or Azure Blob through
an abstraction.

**Stores**

-   raw telemetry
-   cleaned telemetry
-   curated analytics datasets
-   historical features
-   model-training datasets

**Failure**

Kafka retains events until downstream storage catches up.

------------------------------------------------------------------------

### 4.9 pgvector

**Purpose**

Semantic retrieval for AI Fleet Copilot.

**Stores**

-   maintenance manuals
-   DTC explanations
-   fleet policies
-   maintenance procedures
-   vehicle specifications
-   resolved maintenance knowledge

**Does not store**

Raw telemetry.

------------------------------------------------------------------------

### 4.10 ML Service

**Responsibilities**

-   predictive maintenance
-   vehicle risk prediction
-   driver safety scoring
-   feature-based analytics

**Technology**

Python, scikit-learn/PyTorch as appropriate.

**Input**

Feature vectors generated from stream and batch pipelines.

**Output**

Versioned predictions with:

-   vehicle/driver ID
-   score/probability
-   prediction horizon
-   model version
-   inference timestamp

**Failure**

Fall back to deterministic rules for critical real-time detection where
possible. ML failures must not stop telemetry ingestion.

------------------------------------------------------------------------

### 4.11 FastAPI

**Purpose**

Secure application/API layer.

**Responsibilities**

-   authentication
-   authorization
-   tenant isolation
-   pagination
-   rate limiting
-   business operations
-   dashboard APIs
-   ML result APIs
-   Copilot APIs
-   audit logging

**Failure**

Use timeouts, circuit breakers, graceful degradation, and cached read
paths where safe.

------------------------------------------------------------------------

### 4.12 Next.js

**Purpose**

Fleet operations interface.

Core screens:

-   Fleet Overview
-   Live Vehicle Map
-   Risk Center
-   Predictive Maintenance
-   Driver Safety
-   Cost & Utilization
-   AI Fleet Copilot

The browser never connects directly to Kafka or databases.

------------------------------------------------------------------------

### 4.13 AI Fleet Copilot

**Purpose**

Natural-language access to fleet intelligence.

**Architecture**

``` text
User
 |
 v
FastAPI
 |
 v
Agent Runtime
 |
 +--> Fleet tools
 +--> Vehicle health tools
 +--> Maintenance tools
 +--> Driver-score tools
 +--> Cost tools
 +--> pgvector RAG
 |
 v
LLM
 |
 v
Response
```

Write actions require authorization and, where appropriate, explicit
user confirmation.

------------------------------------------------------------------------

## 5. Security Architecture

### Identity

OAuth2/OIDC + JWT.

### Authorization

RBAC with tenant isolation.

### Vehicle communication

mTLS.

### Network

TLS 1.3 for service communication where applicable.

### Storage

AES-256 or cloud-provider equivalent encryption at rest.

### Secrets

Use a secret manager/Vault. Never commit secrets.

### AI

Tool-only access, allowlisted tools, authorization, audit logging, and
confirmation for mutations.

### Privacy

-   synthetic/public data only
-   location masking where appropriate
-   retention policies
-   right-to-erasure workflow
-   audit trail

------------------------------------------------------------------------

## 6. Observability

Use:

-   OpenTelemetry
-   Prometheus
-   Grafana
-   Loki
-   Tempo

Track:

### Kafka

-   throughput
-   consumer lag
-   partition skew
-   broker health

### Flink

-   processing rate
-   watermark lag
-   late events
-   checkpoint duration
-   checkpoint failures
-   backpressure

### MQTT

-   connected clients
-   messages/sec
-   connection failures

### API

-   request count
-   error rate
-   p50/p95/p99
-   endpoint latency

### ML

-   inference latency
-   prediction count
-   model version
-   errors

Correlate using:

-   trace ID
-   event ID
-   vehicle ID

------------------------------------------------------------------------

## 7. Docker Architecture

Local Compose services:

``` text
mqtt
kafka
kafka-ui
flink-jobmanager
flink-taskmanager
postgres
mongodb
redis
minio
simulator
ml-service
backend
copilot
frontend
prometheus
grafana
loki
tempo
```

One-command local setup is a required deliverable.

------------------------------------------------------------------------

## 8. Kubernetes Architecture

Deploy:

-   frontend
-   backend
-   copilot
-   ML service
-   simulator
-   stream-processing jobs
-   ingestion services

Infrastructure:

-   Kafka
-   EMQX
-   PostgreSQL
-   MongoDB
-   Redis
-   object storage
-   observability

Use HPA for stateless services and workload-specific scaling for
Kafka/Flink.

------------------------------------------------------------------------

## 9. Cloud Architecture

Reference cloud: AWS.

Potential mapping:

  Logical component   AWS reference
  ------------------- --------------------------------
  Kubernetes          EKS
  PostgreSQL          RDS PostgreSQL
  Redis               ElastiCache
  Object storage      S3
  Load balancer       ALB
  Registry            ECR
  Secrets             Secrets Manager
  Kafka               MSK or Kubernetes-hosted Kafka

Application code should remain portable.

------------------------------------------------------------------------

## 10. CI/CD

``` text
Git Push
 -> Lint
 -> Unit tests
 -> Coverage
 -> SAST
 -> Dependency scan
 -> Build
 -> Image scan
 -> Integration tests
 -> Contract tests
 -> Security tests
 -> Docker image
 -> Registry
 -> Deployment
```

Tools:

-   GitHub Actions
-   pytest
-   JUnit 5 + Mockito where applicable
-   Testcontainers
-   Pact
-   Cucumber/behave
-   k6
-   Semgrep
-   SonarQube
-   OWASP ZAP
-   Trivy

------------------------------------------------------------------------

## 11. ADR Candidates

1.  Polyglot persistence
2.  Kafka as event backbone
3.  Flink for event-time stream processing
4.  At-least-once + idempotency
5.  Tool-governed AI Copilot

------------------------------------------------------------------------

## 12. Major Risks

1.  Theoretical throughput may not survive actual load.
2.  Accidental PostgreSQL telemetry overload.
3.  MongoDB becoming a raw-event sink.
4.  Parquet small-file explosion.
5.  Incorrect out-of-order processing.
6.  Duplicate alerts.
7.  AI hallucination.
8.  Unauthorized AI actions.
9.  Cloud lock-in.
10. Premature microservice decomposition.

The architecture is designed to make these risks testable rather than
assuming they are solved.
