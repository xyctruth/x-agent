from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal, Protocol
from uuid import uuid4

from x_agent.agent.simple_agent import AgentReply, AgentReplyChunk
from x_agent.application.agent_sessions import (
    AgentSessionNotFoundError,
    AgentSessionRepository,
)
from x_agent.domain.agent_message import AgentMessage


class AgentMessageRepository(Protocol):
    def save(self, message: AgentMessage) -> AgentMessage: ...

    def list_by_session_id(self, session_id: str) -> tuple[AgentMessage, ...]: ...


class AgentExecutor(Protocol):
    def execute(self, message: AgentMessage) -> AgentReply: ...

    def stream_execute(self, message: AgentMessage) -> Iterator[AgentReplyChunk]: ...


@dataclass(frozen=True, slots=True)
class CreateAgentMessageCommand:
    session_id: str
    content: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AgentMessageStreamEvent:
    type: Literal["user_message", "assistant_delta", "assistant_message"]
    message: AgentMessage | None = None
    content_delta: str = ""


class AgentMessageService:
    def __init__(
        self,
        *,
        session_repository: AgentSessionRepository,
        message_repository: AgentMessageRepository,
        agent_executor: AgentExecutor | None = None,
        id_factory: Callable[[], str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._session_repository = session_repository
        self._message_repository = message_repository
        self._agent_executor = agent_executor
        self._id_factory = id_factory or (lambda: str(uuid4()))
        self._clock = clock or (lambda: datetime.now(UTC))

    def create_user_message(self, command: CreateAgentMessageCommand) -> AgentMessage:
        self._ensure_session_exists(command.session_id)
        message = AgentMessage.create_user_message(
            message_id=self._id_factory(),
            session_id=command.session_id,
            content=command.content,
            metadata=command.metadata,
            now=self._clock(),
        )
        return self._message_repository.save(message)

    def send_user_message(self, command: CreateAgentMessageCommand) -> tuple[AgentMessage, ...]:
        user_message = self.create_user_message(command)
        if self._agent_executor is None:
            return (user_message,)

        reply = self._agent_executor.execute(user_message)
        assistant_message = AgentMessage.create_assistant_message(
            message_id=self._id_factory(),
            session_id=command.session_id,
            content=reply.content,
            metadata=reply.metadata,
            now=self._clock(),
        )
        return (user_message, self._message_repository.save(assistant_message))

    def stream_user_message(
        self,
        command: CreateAgentMessageCommand,
    ) -> Iterator[AgentMessageStreamEvent]:
        user_message = self.create_user_message(command)
        yield AgentMessageStreamEvent(type="user_message", message=user_message)
        if self._agent_executor is None:
            return

        content_parts: list[str] = []
        metadata: dict[str, str] = {}
        for chunk in self._agent_executor.stream_execute(user_message):
            if chunk.metadata:
                metadata.update(chunk.metadata)
            if not chunk.content_delta:
                continue
            content_parts.append(chunk.content_delta)
            yield AgentMessageStreamEvent(
                type="assistant_delta",
                content_delta=chunk.content_delta,
            )

        assistant_message = AgentMessage.create_assistant_message(
            message_id=self._id_factory(),
            session_id=command.session_id,
            content="".join(content_parts),
            metadata=metadata,
            now=self._clock(),
        )
        yield AgentMessageStreamEvent(
            type="assistant_message",
            message=self._message_repository.save(assistant_message),
        )

    def list_messages(self, session_id: str) -> tuple[AgentMessage, ...]:
        self._ensure_session_exists(session_id)
        return self._message_repository.list_by_session_id(session_id)

    def _ensure_session_exists(self, session_id: str) -> None:
        if self._session_repository.get_by_id(session_id) is None:
            raise AgentSessionNotFoundError(session_id)
