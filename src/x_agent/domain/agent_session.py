from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class AgentSessionStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class AgentSession:
    id: str
    title: str | None
    status: AgentSessionStatus
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, str] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        title: str | None,
        metadata: dict[str, str] | None = None,
        now: datetime | None = None,
    ) -> "AgentSession":
        created_at = now or datetime.now(UTC)
        return cls(
            id=session_id,
            title=title,
            status=AgentSessionStatus.ACTIVE,
            created_at=created_at,
            updated_at=created_at,
            metadata=metadata or {},
        )
