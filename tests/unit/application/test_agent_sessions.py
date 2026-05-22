from datetime import UTC, datetime

import pytest

from x_agent.application.agent_sessions import (
    AgentSessionNotFoundError,
    AgentSessionService,
    CreateAgentSessionCommand,
)
from x_agent.domain.agent_session import AgentSessionStatus
from x_agent.persistence.in_memory_agent_session_repository import (
    InMemoryAgentSessionRepository,
)


def test_create_session_persists_generated_session() -> None:
    repository = InMemoryAgentSessionRepository()
    now = datetime(2026, 5, 22, 12, 0, tzinfo=UTC)
    service = AgentSessionService(
        repository=repository,
        id_factory=lambda: "session-1",
        clock=lambda: now,
    )

    session = service.create_session(
        CreateAgentSessionCommand(
            title="学习 Agent 架构",
            metadata={"source": "manual"},
        ),
    )

    assert session.id == "session-1"
    assert session.status is AgentSessionStatus.ACTIVE
    assert repository.get_by_id("session-1") == session


def test_get_session_returns_existing_session() -> None:
    repository = InMemoryAgentSessionRepository()
    service = AgentSessionService(repository=repository, id_factory=lambda: "session-1")
    created = service.create_session(CreateAgentSessionCommand())

    found = service.get_session(created.id)

    assert found == created


def test_get_session_raises_when_session_does_not_exist() -> None:
    repository = InMemoryAgentSessionRepository()
    service = AgentSessionService(repository=repository)

    with pytest.raises(AgentSessionNotFoundError):
        service.get_session("missing")
