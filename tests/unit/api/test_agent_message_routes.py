from fastapi.testclient import TestClient

from x_agent.agent.simple_agent import AgentReplyChunk
from x_agent.application.llm import LLMProviderError
from x_agent.main import create_app


class FailingAgentExecutor:
    def execute(self, message: object) -> object:
        raise LLMProviderError("provider unavailable")


class StreamFailingAgentExecutor:
    def execute(self, message: object) -> object:
        raise LLMProviderError("provider unavailable")

    def stream_execute(self, message: object) -> tuple[AgentReplyChunk, ...]:
        raise LLMProviderError("provider unavailable")


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


def test_create_agent_message_returns_502_when_agent_execution_fails() -> None:
    app = create_app()
    app.state.agent_executor = FailingAgentExecutor()
    client = TestClient(app)
    session_id = client.post("/api/v1/agent-sessions", json={}).json()["id"]

    response = client.post(
        f"/api/v1/agent-sessions/{session_id}/messages",
        json={"content": "你好"},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Agent execution failed"}


def test_stream_agent_message_returns_sse_events() -> None:
    client = TestClient(create_app())
    session_id = client.post("/api/v1/agent-sessions", json={}).json()["id"]

    response = client.post(
        f"/api/v1/agent-sessions/{session_id}/messages/stream",
        json={"content": "你好"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "event: user_message" in body
    assert "event: assistant_delta" in body
    assert "event: assistant_message" in body
    assert "event: done" in body
    assert '"role":"user"' in body
    assert '"role":"assistant"' in body


def test_stream_agent_message_returns_404_when_session_missing() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/agent-sessions/missing/messages/stream",
        json={"content": "你好"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Agent session not found"}


def test_stream_agent_message_returns_error_event_when_agent_execution_fails() -> None:
    app = create_app()
    app.state.agent_executor = StreamFailingAgentExecutor()
    client = TestClient(app)
    session_id = client.post("/api/v1/agent-sessions", json={}).json()["id"]

    response = client.post(
        f"/api/v1/agent-sessions/{session_id}/messages/stream",
        json={"content": "你好"},
    )

    assert response.status_code == 200
    assert "event: user_message" in response.text
    assert "event: error" in response.text
    assert '"detail": "Agent execution failed"' in response.text
