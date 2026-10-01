# FleetGuard AI

FleetGuard AI is a connected-vehicle intelligence platform for real-time fleet monitoring, predictive maintenance, risk detection, driver safety, cost analysis, and AI-assisted fleet operations.

The repository contains the FleetGuard AI platform as a single monorepo, including the frontend, backend services, database layer, telemetry pipeline, ML/AI services, infrastructure, testing, and architecture documentation.

The system is designed around a high-volume connected-vehicle environment and uses a polyglot architecture so that each workload is handled by the storage or processing system best suited to it.

---

## What FleetGuard AI Does

FleetGuard AI brings vehicle telemetry, diagnostics, maintenance history, driver behavior, fleet risk, and operational costs into a single platform.

Main capabilities:

- Real-time fleet monitoring
- Live vehicle locations and status
- Vehicle health monitoring
- Predictive maintenance
- Vehicle and fleet risk scoring
- Driver safety analysis
- Trip analysis
- Alerts and incident management
- Fleet cost and utilization analytics
- Historical telemetry analytics
- Knowledge retrieval
- AI Fleet Copilot
- Audit logging
- System health and observability
- Multi-tenant fleet management

---

# System Architecture

```text
                         CONNECTED VEHICLES
                                |
                                v
                              MQTT
                                |
                                v
                             KAFKA
                                |
                                v
                       STREAM PROCESSING
                            FLINK
                                |
             +------------------+------------------+
             |                  |                  |
             v                  v                  v
           REDIS             MONGODB          POSTGRESQL
        Live State          Telemetry        Business Data
        Risk / Alerts       Diagnostics      Organizations
        Locations                           Users / Roles
                                            Fleets / Vehicles
                                            Drivers / Trips
                                            Maintenance
                                            Alerts / Audit
             |                  |                  |
             +------------------+------------------+
                                |
                                v
                       OBJECT STORAGE
                         S3 / PARQUET
                                |
                                v
                    HISTORICAL ANALYTICS
                                |
                                v
                         ML / RISK LAYER
                                |
                    +-----------+-----------+
                    |                       |
                    v                       v
                 pgvector              AI AGENT
              Knowledge Base        Fleet Copilot
                    |                       |
                    +-----------+-----------+
                                |
                                v
                              API
                           FASTAPI
                                |
                                v
                           FRONTEND
                            NEXT.JS
```

The architecture separates high-volume telemetry processing from transactional business workloads while keeping the different data sources connected through clear service boundaries.

---

# Repository Structure

```text
FleetGuard AI/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── pages/
│   ├── services/
│   └── ...
│
├── services/
│   ├── api/
│   │   ├── fleetguard_db/
│   │   ├── migrations/
│   │   ├── routes/
│   │   ├── services/
│   │   └── ...
│   │
│   ├── simulator/
│   │   └── Vehicle telemetry generation
│   │
│   ├── ingestion/
│   │   └── MQTT ingestion and Kafka integration
│   │
│   ├── stream-processor/
│   │   └── Flink streaming jobs and configuration
│   │
│   ├── ml-service/
│   │   └── Risk and predictive-maintenance services
│   │
│   └── ai-agent/
│       └── AI Fleet Copilot and tool integration
│
├── database/
│   ├── postgres/
│   ├── mongodb/
│   └── redis/
│
├── infrastructure/
│   ├── docker/
│   ├── kubernetes/
│   └── terraform/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── database/
│   └── ...
│
├── scripts/
│   └── Developer and environment tooling
│
├── docs/
│   ├── architecture/
│   └── database/
│
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

---

# Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Next.js / React / TypeScript | Fleet operations dashboard |
| API | FastAPI / Python | Backend API boundary |
| Messaging | Kafka | Durable event streaming |
| Device Communication | MQTT / EMQX | Vehicle telemetry ingestion |
| Stream Processing | Apache Flink | Real-time processing |
| Transactional Database | PostgreSQL | Business source of truth |
| Telemetry Database | MongoDB | High-volume telemetry and diagnostics |
| Cache | Redis | Live state and hot read models |
| Object Storage | S3-compatible storage | Historical data lake |
| Analytics Format | Parquet | Columnar historical storage |
| Vector Database | pgvector | Semantic knowledge retrieval |
| ML | Python ML stack | Risk and predictive maintenance |
| AI | AI Agent / Tool Layer | Fleet Copilot |
| Migrations | Alembic | PostgreSQL schema migrations |
| Testing | Pytest / Testcontainers | Unit and integration testing |
| Observability | Prometheus / Grafana | Metrics and monitoring |
| Containers | Docker / Docker Compose | Local deployment |
| Infrastructure | Kubernetes / Terraform | Deployment boundaries |

---

# Data Architecture

FleetGuard AI uses different storage systems for different workloads.

## PostgreSQL

PostgreSQL is the transactional source of truth.

It stores:

```text
Organizations
Users
Roles
Permissions
Fleets
Vehicles
Drivers
Trips
Maintenance Records
Alerts
Subscriptions
Audit Logs
Risk Summaries
Cost Summaries
```

PostgreSQL provides:

- Foreign-key relationships
- Transactional consistency
- Constraints
- Indexes
- 3NF relational design
- Tenant isolation
- Migration management
- Auditability

---

## MongoDB

MongoDB handles high-volume operational telemetry and diagnostics.

Main collections:

```text
telemetry_events
diagnostic_events
```

Telemetry can include:

```text
event_id
organization_id
vehicle_id
timestamp
latitude
longitude
speed
heading
odometer
battery_soc
battery_soh
temperature
fuel_level
dtc_codes
event_type
sequence_number
```

MongoDB is intended for recent operational telemetry rather than transactional business records.

---

## Redis

Redis provides fast access to frequently changing operational state.

Representative keys include:

```text
fg:vehicle:{vehicle_id}:state
fg:vehicle:{vehicle_id}:risk
fg:locations:{fleet_id}
fg:alerts:active:{fleet_id}
fg:alert:{alert_id}
fg:fleet:{fleet_id}:summary
fg:rate:{user_id}:{endpoint}:{minute}
fg:dedup:event:{event_id}
```

Redis is a disposable read model and is not treated as the source of truth.

---

## S3-Compatible Storage and Parquet

Historical telemetry is stored in an object-storage data lake.

Logical datasets:

```text
raw/
cleaned/
curated/
ml/
```

The intended partitioning strategy is:

```text
event_date/
hour/
vehicle_bucket/
```

Vehicle buckets avoid creating a separate partition for every vehicle and help control the number of small files.

---

## pgvector

pgvector provides semantic retrieval for the AI layer.

Knowledge can include:

```text
Maintenance Manuals
DTC Explanations
Vehicle Specifications
Maintenance Procedures
Fleet Policies
Resolved Maintenance Knowledge
```

The retrieval pipeline is:

```text
Document
    |
    v
Document Chunk
    |
    v
Embedding
    |
    v
pgvector
    |
    v
Semantic Search
    |
    v
AI Fleet Copilot
```

Detailed database architecture is available in:

`docs/database/DATABASE_DESIGN.md`

---

# Core Application Modules

## Fleet Dashboard

Provides:

- Total vehicles
- Fleet health
- Active alerts
- Risk distribution
- Maintenance status
- Cost trends
- Utilization
- Recent activity

## Live Fleet

Provides:

- Live vehicle locations
- Vehicle status
- Risk state
- Fleet filtering
- Vehicle search
- Location visualization

## Vehicle Management

Vehicle detail includes:

- Vehicle information
- Current state
- Telemetry
- Diagnostics
- DTCs
- Risk history
- Maintenance history
- Alerts
- Trip history

## Driver Management

Provides:

- Driver profiles
- Vehicle assignments
- Safety scores
- Harsh braking
- Harsh acceleration
- Trip statistics
- Driver activity

## Predictive Maintenance

Provides:

- Vehicle health
- Component risk
- Failure probability
- Maintenance history
- Upcoming maintenance
- Risk factors
- Model information

## Risk Center

Provides:

- Fleet-level risk
- Vehicle-level risk
- Risk scores
- Risk levels
- Contributing factors
- Historical risk trends

## Alerts

Supports:

- Critical alerts
- High-risk alerts
- Alert acknowledgement
- Alert resolution
- Alert history
- Alert timelines
- Vehicle and fleet relationships

## Cost and Utilization

Tracks:

- Fuel cost
- Energy cost
- Maintenance cost
- Idle cost
- Total cost
- Cost per kilometer
- Vehicle utilization
- Fleet utilization

## AI Fleet Copilot

The Copilot is designed around controlled operational tools.

Example tools include:

```text
Fleet Risk Tool
Vehicle Health Tool
Maintenance Tool
Cost Analytics Tool
Knowledge Retrieval Tool
```

The agent can combine structured fleet data with retrieved operational knowledge.

---

# Service Architecture

The repository separates responsibilities into services.

```text
services/
│
├── api/
│   └── Application API and database access
│
├── simulator/
│   └── Connected vehicle event generation
│
├── ingestion/
│   └── MQTT and Kafka ingestion
│
├── stream-processor/
│   └── Real-time event processing
│
├── ml-service/
│   └── Risk and predictive maintenance
│
└── ai-agent/
    └── Fleet Copilot and AI tools
```

The intended event flow is:

```text
Vehicle
   |
   v
MQTT
   |
   v
Kafka
   |
   v
Flink
   |
   +----> Redis
   |
   +----> MongoDB
   |
   +----> PostgreSQL
   |
   +----> S3 / Parquet
   |
   +----> ML
             |
             v
          Risk Data
             |
             v
        AI Fleet Copilot
```

---

# Local Development

## Prerequisites

- Docker Desktop
- Docker Compose v2
- Python 3.10+

Check versions:

```powershell
docker --version
docker compose version
python --version
```

---

# Start the Platform

From the repository root:

```powershell
python scripts/dev.py up
```

The developer launcher:

- Creates `.env` when required
- Generates development credentials
- Builds containers
- Starts infrastructure
- Creates database roles
- Installs pgvector
- Configures MongoDB
- Configures Redis
- Runs Alembic migrations
- Seeds development data

---

# Local Endpoints

| Component | Address |
|---|---|
| Frontend | http://localhost:3000 |
| API Health | http://localhost:8000/healthz |
| Kafka UI | http://localhost:8080 |
| Flink UI | http://localhost:8081 |
| S3-compatible Storage | http://localhost:8333 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |
| MQTT | `mqtt://localhost:1883` |
| Kafka | `localhost:9092` |

PostgreSQL, MongoDB, and Redis are kept inside the private Docker network and do not require host-published ports for normal application operation.

---

# Developer Commands

Start:

```powershell
python scripts/dev.py up
```

Stop containers while preserving data:

```powershell
python scripts/dev.py stop
```

Remove containers and networks:

```powershell
python scripts/dev.py down
```

View logs:

```powershell
python scripts/dev.py logs
```

View running services:

```powershell
python scripts/dev.py ps
```

Verify local infrastructure:

```powershell
python scripts/dev.py verify
```

Run migrations:

```powershell
python scripts/dev.py migrate
```

Seed data:

```powershell
python scripts/dev.py seed 100
```

---

# Make Commands

```powershell
make up
make down
make stop
make logs
make ps
make migrate
make seed SEED_VEHICLE_COUNT=100
make test-database
```

---

# Database Design

The database design follows a clear separation of responsibilities.

```text
PostgreSQL
    |
    +-- Business Data
    +-- Access Control
    +-- Maintenance
    +-- Alerts
    +-- Risk Summaries
    +-- Cost Summaries
    +-- Audit Logs

MongoDB
    |
    +-- Telemetry
    +-- Diagnostics

Redis
    |
    +-- Latest State
    +-- Locations
    +-- Risk
    +-- Active Alerts
    +-- Fleet Summaries
    +-- Cache

S3 / Parquet
    |
    +-- Raw Telemetry
    +-- Cleaned Telemetry
    +-- Curated Data
    +-- ML Datasets

pgvector
    |
    +-- Documents
    +-- Chunks
    +-- Embeddings
```

The detailed database design is documented in:

```text
docs/database/DATABASE_DESIGN.md
```

---

# Security

The platform is designed around:

- OAuth2/OIDC
- JWT authentication
- Role-based access control
- Tenant isolation
- mTLS for appropriate device/service communication
- TLS for service communication
- Encryption at rest
- Secret management
- Audit logging
- Location-data protection
- Data retention policies
- Right-to-erasure workflows

The local environment intentionally uses development-only credentials and protocols.

Production deployments should replace these with hardened authentication, TLS, secret management, private networking, and production-grade access controls.

---

# Configuration

Configuration is provided through:

```text
.env
.env.example
```

Never commit:

```text
.env
```

The `.env.example` file contains configuration names without storing secret values.

---

# Testing

Install test dependencies:

```powershell
python -m pip install -r tests/requirements.txt
```

Run tests:

```powershell
python -m pytest
```

Database integration tests use Testcontainers and require Docker.

The test structure is intended to support:

```text
Unit Tests
Integration Tests
Database Tests
API Tests
Contract Tests
End-to-End Tests
Performance Tests
Security Tests
```

---

# Observability

The platform includes infrastructure for:

- Prometheus
- Grafana
- Application metrics
- Service health
- Kafka consumer lag
- Processing latency
- API latency
- Error rates
- Database performance
- Redis health
- Stream-processing health

The observability layer is designed to provide a common view across the platform rather than monitoring each service independently.

---

# Performance Targets

The architecture is designed around the hackathon scale requirements.

Target characteristics include:

```text
100,000+ connected vehicles
100,000+ events/sec
3x burst capacity for 5 minutes
<2 sec dashboard target
<5 sec critical alert target
p95 API latency <200 ms
p99 API latency <500 ms
99.9% availability target
```

These are architectural targets and are not presented as measured production results.

Actual throughput and latency should be established through dedicated load and resilience testing.

---

# Reliability and Data Consistency

Different data classes have different consistency requirements.

### Strong consistency

Used for:

- Organizations
- Users
- Roles
- Permissions
- Vehicle ownership
- Maintenance records
- Alert lifecycle
- Subscriptions
- Audit records

### Eventual consistency

Used for:

- Live vehicle state
- Redis summaries
- Risk summaries
- Historical telemetry
- Parquet datasets
- Embeddings
- Analytics read models

The streaming architecture uses at-least-once delivery.

Therefore, consumers must handle:

- Duplicate events
- Out-of-order events
- Retries
- Consumer restarts
- Partial failures

Event IDs and sequence numbers provide the foundation for idempotent processing.

---

# Multi-Tenancy

FleetGuard AI is designed as a multi-tenant system.

Tenant-owned records carry:

```text
organization_id
```

Tenant isolation is enforced through:

- API authorization
- Repository-level filtering
- Role-based access control
- Organization-scoped queries
- Optional PostgreSQL Row-Level Security

The same isolation model applies to AI tools so that the Copilot cannot access data belonging to another organization.

---

# AI Safety

The AI Fleet Copilot is designed to operate through explicit tools instead of unrestricted database access.

The intended flow is:

```text
User
 |
 v
AI Fleet Copilot
 |
 +--> Permission Check
 |
 +--> Tool Selection
 |
 +--> Fleet Risk
 |
 +--> Vehicle Health
 |
 +--> Maintenance
 |
 +--> Cost Analytics
 |
 +--> Knowledge Retrieval
 |
 v
Grounded Response
```

AI-agent actions should be auditable and high-impact operations should require explicit human confirmation.

---

# Current Implementation

The repository currently contains the platform foundation and service boundaries for the complete FleetGuard AI architecture.

Available infrastructure includes:

- Docker Compose environment
- PostgreSQL
- Alembic migrations
- pgvector
- MongoDB
- Redis
- Kafka
- MQTT
- Flink
- S3-compatible object storage
- Prometheus
- Grafana
- Database seeding
- Database integration testing
- Frontend application structure
- FastAPI service structure
- ML service boundary
- AI-agent service boundary
- Vehicle simulator boundary
- Ingestion service boundary
- Kubernetes deployment boundary
- Terraform infrastructure boundary

The remaining service workflows can be developed independently while keeping the same architecture and data contracts.

---

# Known Limitations

The local environment is a development environment and is not intended to represent the final production deployment.

Current limitations include:

- Complete telemetry generation and ingestion workflows are still under development.
- Full MQTT-to-Kafka bridging is not yet implemented.
- Production Flink processing jobs are not yet complete.
- ML training and production inference workflows are not complete.
- Complete AI-agent tool execution is not complete.
- Full business API workflows are not complete.
- Redis is currently a single-node deployment.
- Kafka is configured as a local development broker.
- Production device authentication and ACLs are not configured locally.
- Complete Kafka-to-Parquet pipelines are not yet implemented.
- Data retention and compaction jobs are not yet complete.
- Application-level observability instrumentation is still being developed.
- Kubernetes and Terraform configurations represent deployment boundaries rather than a production cloud deployment.
- Full 100,000-vehicle scale testing has not been performed in the local environment.
- Production security, availability, throughput, and latency have not been independently validated.

The architecture and implementation should therefore be evaluated according to the functionality actually present in the repository rather than treating development infrastructure as production validation.

---

# Object Storage

The intended architecture uses MinIO as the S3-compatible object-storage layer.

For local development, SeaweedFS 4.48 is currently used as an S3-compatible substitute because the required MinIO public registries and binary archive were unavailable during setup.

The application interacts with the S3-compatible interface, keeping the storage abstraction independent from the specific local provider.

---

# Documentation

Architecture documentation:

```text
docs/architecture/
```

Database documentation:

```text
docs/database/DATABASE_DESIGN.md
```

The documentation covers:

- System architecture
- Service boundaries
- Data flow
- Database schema
- ER model
- PostgreSQL design
- MongoDB telemetry model
- Redis key design
- Parquet layout
- pgvector architecture
- Indexing strategy
- Query patterns
- Pagination
- Materialized views
- N+1 prevention
- Migration strategy
- Architecture decisions

---

# Development Roadmap

```text
Phase 1
Infrastructure
      |
      v
Phase 2
Database & Persistence
      |
      v
Phase 3
Vehicle Simulator
      |
      v
Phase 4
MQTT + Kafka Ingestion
      |
      v
Phase 5
Flink Stream Processing
      |
      v
Phase 6
Risk & Predictive Maintenance
      |
      v
Phase 7
Business API
      |
      v
Phase 8
Frontend Workflows
      |
      v
Phase 9
AI Fleet Copilot
      |
      v
Phase 10
Load, Resilience & Security Testing
```

---

# Project Goals

FleetGuard AI is built around five main goals:

1. Process connected-vehicle data at fleet scale.
2. Detect operational and vehicle risk in near real time.
3. Turn telemetry into actionable predictive-maintenance insights.
4. Provide a unified operational interface for fleet teams.
5. Use AI to make fleet information easier to query and understand.

The architecture is intentionally modular so that telemetry processing, business operations, analytics, machine learning, and AI can evolve independently while sharing consistent data contracts.

---

# License

Add the applicable project license here.
