# FleetGuard AI

FleetGuard AI is a monorepo for the connected-vehicle platform described in `docs/architecture/`. Phases 1 and 2 establish the local stack and database layer. Telemetry ingestion, stream-processing jobs, model inference/training, business API endpoints, and user-facing workflows are not implemented yet.

## Start locally

Prerequisites: Docker Desktop with Docker Compose v2 and Python 3.10+.

From the repository root, run one command:

```powershell
python scripts/dev.py up
```

The command creates an ignored `.env` on first run, generates local-only credentials, builds images, starts infrastructure, provisions least-privilege database roles, installs pgvector, creates MongoDB validators/indexes, runs Alembic migrations, and seeds the configured development dataset. Set `SEED_VEHICLE_COUNT` in `.env` before the first initialization (1–10,000); the default is 10. To stop containers while keeping data, run `python scripts/dev.py stop`. To stop and remove containers/networks but preserve named volumes, run `python scripts/dev.py down`. `docker compose down -v` also deletes local persisted data.

The stack uses development-only protocols on a private Docker network. Only app UIs, MQTT, Kafka's local listener, and the S3-compatible object endpoint are bound to loopback. PostgreSQL, MongoDB, and Redis have no host-published ports. PostgreSQL/MongoDB runtime roles are separate from admin and migration roles; Redis requires a generated password.

## Local endpoints

| Component | URL / address |
| --- | --- |
| Frontend | http://localhost:3000 |
| API health | http://localhost:8000/healthz |
| Kafka UI | http://localhost:8080 |
| Flink UI | http://localhost:8081 |
| S3-compatible object storage | http://localhost:8333 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |
| MQTT | `mqtt://localhost:1883` |
| Kafka | `localhost:9092` |

Grafana credentials are generated into `.env` at first startup. Treat `.env` as a local secret and never commit it.

## Structure

```text
frontend/                 Next.js application shell
services/api/             FastAPI boundary
services/simulator/       simulator service shell
services/ingestion/       MQTT-to-Kafka service shell
services/stream-processor/ Flink image/configuration
services/ml-service/      inference service shell
services/ai-agent/        agent service shell
database/{postgres,mongodb,redis}/  persistence ownership placeholders
services/api/fleetguard_db/ database settings, models, repositories, adapters
services/api/migrations/ Alembic configuration and revisions
infrastructure/docker/    local observability configuration
infrastructure/kubernetes/ Kubernetes configuration boundary
infrastructure/terraform/ infrastructure-as-code boundary
tests/                    initial service checks
scripts/                  developer tooling
```

## Developer commands

Use `python scripts/dev.py up|down|stop|logs|ps|verify|migrate`. Run `python scripts/dev.py seed 100` to seed a different quantity in a fresh development database. Equivalent Make targets include `make up`, `make down`, `make stop`, `make logs`, `make ps`, `make migrate`, `make seed SEED_VEHICLE_COUNT=100`, and `make test-database` where Make is installed. `python scripts/dev.py verify` checks container health and connections using application credentials.

Run unit and database integration tests with `python -m pip install -r tests/requirements.txt` and `python -m pytest`. The database tests use Testcontainers and need Docker.

## Security and configuration

`.env.example` documents local variables without storing secret values. The developer launcher generates local credentials and URL-encodes DSNs. Service addresses and credentials are injected through Compose environment variables. Local Kafka and MQTT use plaintext and are intended only for development; production must use a secret manager, TLS/authenticated endpoints, private networking, and hardened service-specific configuration. Do not use generated development credentials outside this machine.

## Current limitations

- Simulator, ingestion, ML, AI-agent, and API business endpoints remain service shells. Telemetry generation, MQTT-to-Kafka bridging, stream processing, and inference are not implemented.
- Flink starts with a task manager but has no submitted processing job or checkpoint policy.
- Kafka is a single-node KRaft broker with replication factor one; this is not a durability or throughput test environment.
- Local EMQX/Kafka are development-only and do not configure production device identity, ACLs, SASL, or TLS.
- PostgreSQL has a normalized business schema and pgvector extension; application authentication/authorization and public business API endpoints are not implemented.
- MongoDB stores validated operational telemetry documents, but there is no live telemetry producer/ingestion pipeline yet.
- Redis is a single-node cache; it is not the source of truth and is not clustered.
- Parquet output is available as an API utility, but Kafka-to-object-store writing, compaction, retention jobs, and batch analytics are not implemented.
- Observability containers and Grafana data sources are provisioned, but application metrics, log shipping, traces, dashboards, and alert rules are not yet instrumented.
- The architecture specifies MinIO, but its public image registries and binary archive were unavailable during setup. Local development therefore uses SeaweedFS 4.48 as an S3-compatible object-storage substitute; production/provider choice remains unchanged.
- Kubernetes and Terraform directories mark future deployment boundaries only; no cloud resources or production deployment are provisioned.
- No 100,000-vehicle scale, throughput, latency, availability, or security target is claimed or tested in this phase.

Database model details, ER diagram, indexes, query patterns, Parquet layout, and migration decisions are in [docs/database/DATABASE_DESIGN.md](docs/database/DATABASE_DESIGN.md).
