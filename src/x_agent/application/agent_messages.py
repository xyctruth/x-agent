from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from x_agent.application.agent_sessions import (
    AgentSessionNotFoundError,
    AgentSessionRepository,
)
from x_agent.domain.agent_message import AgentMessage


class AgentMessageRepository(Protocol):
    def save(self, message: AgentMessage) -> AgentMessage: ...

    def list_by_session_id(self, session_id: str) -> tuple[AgentMessage, ...]: ...


@dataclass(frozen=True, slots=True)
class CreateAgentMessageCommand:
    session_id: str
    content: str
    metadata: dict[str, str] = field(default_factory=dict)


class AgentMessageService:
    def __init__(
        self,
        *,
        session_repository: AgentSessionRepository,
        message_repository: AgentMessageRepository,
        id_factory: Callable[[], str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._session_repository = session_repository
        self._message_repository = message_repository
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

    def list_messages(self, session_id: str) -> tuple[AgentMessage, ...]:
        self._ensure_session_exists(session_id)
        return self._message_repository.list_by_session_id(session_id)

    def _ensure_session_exists(self, session_id: str) -> None:
        if self._session_repository.get_by_id(session_id) is None:
            raise AgentSessionNotFoundError(session_id)
