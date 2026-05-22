from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from x_agent.domain.agent_message import AgentMessageRole
from x_agent.domain.agent_session import AgentSessionStatus


class HealthResponse(BaseModel):
    service: str
    version: str
    status: str


class ReadinessResponse(BaseModel):
    status: str


class ServiceInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    version: str
    responsibilities: tuple[str, ...]
    layers: tuple[str, ...]


class AgentSessionCreateRequest(BaseModel):
    title: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class AgentSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None
    status: AgentSessionStatus
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, str]


class AgentMessageCreateRequest(BaseModel):
    content: str = Field(min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class AgentMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    role: AgentMessageRole
    content: str
    created_at: datetime
    metadata: dict[str, str]
