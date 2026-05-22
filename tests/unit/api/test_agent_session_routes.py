from fastapi.testclient import TestClient

from x_agent.main import create_app


def test_create_agent_session_returns_created_session() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/agent-sessions",
        json={
            "title": "学习 Agent 架构",
            "metadata": {"source": "manual"},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["title"] == "学习 Agent 架构"
    assert body["status"] == "active"
    assert body["created_at"]
    assert body["updated_at"]
    assert body["metadata"] == {"source": "manual"}


def test_get_agent_session_returns_existing_session() -> None:
    client = TestClient(create_app())
    create_response = client.post("/api/v1/agent-sessions", json={})
    session_id = create_response.json()["id"]

    response = client.get(f"/api/v1/agent-sessions/{session_id}")

    assert response.status_code == 200
    assert response.json()["id"] == session_id


def test_get_agent_session_returns_404_when_missing() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/agent-sessions/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "Agent session not found"}
