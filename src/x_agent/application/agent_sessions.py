from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from x_agent.domain.agent_session import AgentSession


class AgentSessionNotFoundError(Exception):
    def __init__(self, session_id: str) -> None:
        super().__init__(f"Agent session not found: {session_id}")
        self.session_id = session_id


class AgentSessionRepository(Protocol):
    def save(self, session: AgentSession) -> AgentSession: ...

    def get_by_id(self, session_id: str) -> AgentSession | None: ...


@dataclass(frozen=True, slots=True)
class CreateAgentSessionCommand:
    title: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


class AgentSessionService:
    def __init__(
        self,
        *,
        repository: AgentSessionRepository,
        id_factory: Callable[[], str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._id_factory = id_factory or (lambda: str(uuid4()))
        self._clock = clock or (lambda: datetime.now(UTC))

    def create_session(self, command: CreateAgentSessionCommand) -> AgentSession:
        session = AgentSession.create(
            session_id=self._id_factory(),
            title=command.title,
            metadata=command.metadata,
            now=self._clock(),
        )
        return self._repository.save(session)

    def get_session(self, session_id: str) -> AgentSession:
        session = self._repository.get_by_id(session_id)
        if session is None:
            raise AgentSessionNotFoundError(session_id)
        return session
