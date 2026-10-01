# API Overview

Base URL: `http://localhost:8000`

- `GET /vehicles` - list vehicles
- `GET /vehicles/{vin}` - vehicle detail
- `GET /telemetry/{vin}/latest` - latest telemetry points
- `GET /alerts` - active alerts
- `GET /maintenance/predict/{vin}` - predictive maintenance forecast
- `GET /analytics/kpis` - fleet KPIs
- `POST /copilot/ask` - ask the AI Fleet Copilot

See `docs/examples/` for sample responses.
