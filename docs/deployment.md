# Deployment

- `compose.yaml` for local development.
- Docker images per service under `services/*/Dockerfile`.
- Kubernetes manifests under `infrastructure/kubernetes`.
- Terraform modules under `infrastructure/terraform`.
- Observability: Prometheus, Grafana, Loki, Tempo (see `infrastructure/docker/development`).
