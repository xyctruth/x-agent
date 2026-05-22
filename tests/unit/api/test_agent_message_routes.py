from fastapi.testclient import TestClient

from x_agent.main import create_app


def test_create_agent_message_returns_created_user_message() -> None:
    client = TestClient(create_app())
    session_id = client.post("/api/v1/agent-sessions", json={}).json()["id"]

    response = client.post(
        f"/api/v1/agent-sessions/{session_id}/messages",
        json={
            "content": "你好",
            "metadata": {"client": "web"},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["session_id"] == session_id
    assert body["role"] == "user"
    assert body["content"] == "你好"
    assert body["created_at"]
    assert body["metadata"] == {"client": "web"}


def test_list_agent_messages_returns_session_messages() -> None:
    client = TestClient(create_app())
    session_id = client.post("/api/v1/agent-sessions", json={}).json()["id"]
    client.post(
        f"/api/v1/agent-sessions/{session_id}/messages",
        json={"content": "第一条"},
    )
    client.post(
        f"/api/v1/agent-sessions/{session_id}/messages",
        json={"content": "第二条"},
    )

    response = client.get(f"/api/v1/agent-sessions/{session_id}/messages")

    assert response.status_code == 200
    body = response.json()
    assert [message["content"] for message in body] == ["第一条", "第二条"]


def test_create_agent_message_returns_404_when_session_missing() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/agent-sessions/missing/messages",
        json={"content": "你好"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Agent session not found"}


def test_list_agent_messages_returns_404_when_session_missing() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/agent-sessions/missing/messages")

    assert response.status_code == 404
    assert response.json() == {"detail": "Agent session not found"}
