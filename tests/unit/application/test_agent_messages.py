from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from x_agent.agent.simple_agent import AgentReply, AgentReplyChunk, SimpleAgent
from x_agent.application.agent_messages import (
    AgentMessageService,
    CreateAgentMessageCommand,
)
from x_agent.application.agent_sessions import (
    AgentSessionNotFoundError,
    AgentSessionService,
    CreateAgentSessionCommand,
)
from x_agent.domain.agent_message import AgentMessageRole
from x_agent.execution.agent_executor import AgentExecutor
from x_agent.persistence.in_memory_agent_message_repository import (
    InMemoryAgentMessageRepository,
)
from x_agent.persistence.in_memory_agent_session_repository import (
    InMemoryAgentSessionRepository,
)


class StreamingAgentExecutor:
    def execute(self, message: object) -> AgentReply:
        return AgentReply(content="完整回复", metadata={"agent": "fake"})

    def stream_execute(self, message: object) -> Iterator[AgentReplyChunk]:
        yield AgentReplyChunk(content_delta="流式")
        yield AgentReplyChunk(
            content_delta="回复",
            metadata={"agent": "fake", "mode": "stream"},
        )


def test_create_user_message_persists_message_for_existing_session() -> None:
    session_repository = InMemoryAgentSessionRepository()
    message_repository = InMemoryAgentMessageRepository()
    session_service = AgentSessionService(
        repository=session_repository,
        id_factory=lambda: "session-1",
    )
    session_service.create_session(CreateAgentSessionCommand())
    now = datetime(2026, 5, 22, 13, 0, tzinfo=UTC)
    message_service = AgentMessageService(
        session_repository=session_repository,
        message_repository=message_repository,
        id_factory=lambda: "message-1",
        clock=lambda: now,
    )

    message = message_service.create_user_message(
        CreateAgentMessageCommand(
            session_id="session-1",
            content="你好",
            metadata={"client": "web"},
        ),
    )

    assert message.id == "message-1"
    assert message.role is AgentMessageRole.USER
    assert message.created_at == now
    assert message_repository.list_by_session_id("session-1") == (message,)


def test_send_user_message_persists_user_and_assistant_messages() -> None:
    session_repository = InMemoryAgentSessionRepository()
    message_repository = InMemoryAgentMessageRepository()
    AgentSessionService(
        repository=session_repository,
        id_factory=lambda: "session-1",
    ).create_session(CreateAgentSessionCommand())
    message_ids = iter(("message-1", "message-2"))
    message_service = AgentMessageService(
        session_repository=session_repository,
        message_repository=message_repository,
        agent_executor=AgentExecutor(agent=SimpleAgent()),
        id_factory=lambda: next(message_ids),
    )

    messages = message_service.send_user_message(
        CreateAgentMessageCommand(session_id="session-1", content="你好"),
    )

    assert [message.role for message in messages] == [
        AgentMessageRole.USER,
        AgentMessageRole.ASSISTANT,
    ]
    assert messages[0].content == "你好"
    assert "你好" in messages[1].content
    assert message_repository.list_by_session_id("session-1") == messages


def test_stream_user_message_persists_user_and_assistant_messages() -> None:
    session_repository = InMemoryAgentSessionRepository()
    message_repository = InMemoryAgentMessageRepository()
    AgentSessionService(
        repository=session_repository,
        id_factory=lambda: "session-1",
    ).create_session(CreateAgentSessionCommand())
    message_ids = iter(("message-1", "message-2"))
    message_service = AgentMessageService(
        session_repository=session_repository,
        message_repository=message_repository,
        agent_executor=StreamingAgentExecutor(),
        id_factory=lambda: next(message_ids),
    )

    events = tuple(
        message_service.stream_user_message(
            CreateAgentMessageCommand(session_id="session-1", content="你好"),
        ),
    )

    assert [event.type for event in events] == [
        "user_message",
        "assistant_delta",
        "assistant_delta",
        "assistant_message",
    ]
    assert events[0].message is not None
    assert events[0].message.content == "你好"
    assert events[1].content_delta == "流式"
    assert events[2].content_delta == "回复"
    assert events[3].message is not None
    assert events[3].message.content == "流式回复"
    assert events[3].message.metadata == {"agent": "fake", "mode": "stream"}
    assert message_repository.list_by_session_id("session-1") == (
        events[0].message,
        events[3].message,
    )


def test_create_user_message_raises_when_session_does_not_exist() -> None:
    message_service = AgentMessageService(
        session_repository=InMemoryAgentSessionRepository(),
        message_repository=InMemoryAgentMessageRepository(),
    )

    with pytest.raises(AgentSessionNotFoundError):
        message_service.create_user_message(
            CreateAgentMessageCommand(session_id="missing", content="你好"),
        )


def test_list_messages_returns_messages_in_creation_order() -> None:
    session_repository = InMemoryAgentSessionRepository()
    message_repository = InMemoryAgentMessageRepository()
    AgentSessionService(
        repository=session_repository,
        id_factory=lambda: "session-1",
    ).create_session(CreateAgentSessionCommand())
    message_ids = iter(("message-1", "message-2"))
    message_service = AgentMessageService(
        session_repository=session_repository,
        message_repository=message_repository,
        id_factory=lambda: next(message_ids),
    )
    first = message_service.create_user_message(
        CreateAgentMessageCommand(session_id="session-1", content="第一条"),
    )
    second = message_service.create_user_message(
        CreateAgentMessageCommand(session_id="session-1", content="第二条"),
    )

    messages = message_service.list_messages("session-1")

    assert messages == (first, second)
