from datetime import UTC, datetime

from x_agent.domain.agent_message import AgentMessage, AgentMessageRole


def test_create_user_message_uses_user_role_and_given_time() -> None:
    now = datetime(2026, 5, 22, 13, 0, tzinfo=UTC)

    message = AgentMessage.create_user_message(
        message_id="message-1",
        session_id="session-1",
        content="你好",
        metadata={"client": "web"},
        now=now,
    )

    assert message.id == "message-1"
    assert message.session_id == "session-1"
    assert message.role is AgentMessageRole.USER
    assert message.content == "你好"
    assert message.created_at == now
    assert message.metadata == {"client": "web"}


def test_create_user_message_defaults_metadata_to_empty_dict() -> None:
    message = AgentMessage.create_user_message(
        message_id="message-1",
        session_id="session-1",
        content="你好",
    )

    assert message.metadata == {}
