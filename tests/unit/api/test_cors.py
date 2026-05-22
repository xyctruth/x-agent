from fastapi.testclient import TestClient

from x_agent.main import create_app


def test_cors_preflight_allows_configured_web_origin() -> None:
    client = TestClient(create_app())

    response = client.options(
        "/api/v1/agent-sessions",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
