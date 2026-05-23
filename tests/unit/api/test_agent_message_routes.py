from fastapi.testclient import TestClient

from x_agent.main import create_app


def test_create_agent_message_returns_created_user_and_assistant_messages() -> None:
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
    messages = body["messages"]
    assert len(messages) == 2
    assert messages[0]["id"]
    assert messages[0]["session_id"] == session_id
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "你好"
    assert messages[0]["created_at"]
    assert messages[0]["metadata"] == {"client": "web"}
    assert messages[1]["role"] == "assistant"
    assert "你好" in messages[1]["content"]
    assert messages[1]["metadata"] == {
        "agent": "simple",
        "mode": "deterministic",
    }


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
    assert [message["role"] for message in body] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert body[0]["content"] == "第一条"
    assert "第一条" in body[1]["content"]
    assert body[2]["content"] == "第二条"
    assert "第二条" in body[3]["content"]


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
