# PostgreSQL

PostgreSQL 16 with pgvector is provisioned by the root Compose file with persistent storage. The API owns the normalized transactional schema and Alembic revisions under `services/api/`. Admin, migration-owner, and runtime credentials are distinct and generated into ignored `.env` for local development. See [docs/database/DATABASE_DESIGN.md](../../docs/database/DATABASE_DESIGN.md).