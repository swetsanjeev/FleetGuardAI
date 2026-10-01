# MongoDB

MongoDB is the operational telemetry/diagnostic document store. The API database package creates validated `telemetry_events` and `diagnostic_events` collections and query indexes. MongoDB uses a separate runtime user scoped to the FleetGuard database. See [docs/database/DATABASE_DESIGN.md](../../docs/database/DATABASE_DESIGN.md).