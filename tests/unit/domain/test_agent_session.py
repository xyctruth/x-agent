from datetime import UTC, datetime

from x_agent.domain.agent_session import AgentSession, AgentSessionStatus


def test_create_agent_session_uses_active_status_and_given_time() -> None:
    now = datetime(2026, 5, 22, 12, 0, tzinfo=UTC)

    session = AgentSession.create(
        session_id="session-1",
        title="学习 Agent 架构",
        metadata={"source": "manual"},
        now=now,
    )

    assert session.id == "session-1"
    assert session.title == "学习 Agent 架构"
    assert session.status is AgentSessionStatus.ACTIVE
    assert session.created_at == now
    assert session.updated_at == now
    assert session.metadata == {"source": "manual"}


def test_create_agent_session_defaults_metadata_to_empty_dict() -> None:
    session = AgentSession.create(
        session_id="session-1",
        title=None,
    )

    assert session.metadata == {}
