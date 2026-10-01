from fastapi.testclient import TestClient

from services.api.main import app


def test_health_endpoint_reports_service_status() -> None:
    response = TestClient(app).get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api"}