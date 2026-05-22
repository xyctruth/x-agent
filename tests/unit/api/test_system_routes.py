from fastapi.testclient import TestClient

from x_agent.main import create_app


def test_healthz_returns_liveness_metadata() -> None:
    client = TestClient(create_app())

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "service": "x-agent",
        "version": "0.1.0",
        "status": "ok",
    }


def test_readyz_returns_ready_status() -> None:
    client = TestClient(create_app())

    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_service_info_returns_layer_boundaries() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/service-info")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "x-agent"
    assert "service metadata" in body["responsibilities"]
    assert body["layers"] == [
        "client",
        "api",
        "application",
        "domain",
        "agent",
        "execution",
        "persistence",
        "infrastructure",
    ]
