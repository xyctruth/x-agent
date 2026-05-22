from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class AgentMessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class AgentMessage:
    id: str
    session_id: str
    role: AgentMessageRole
    content: str
    created_at: datetime
    metadata: dict[str, str] = field(default_factory=dict)

    @classmethod
    def create_user_message(
        cls,
        *,
        message_id: str,
        session_id: str,
        content: str,
        metadata: dict[str, str] | None = None,
        now: datetime | None = None,
    ) -> "AgentMessage":
        return cls(
            id=message_id,
            session_id=session_id,
            role=AgentMessageRole.USER,
            content=content,
            created_at=now or datetime.now(UTC),
            metadata=metadata or {},
        )
