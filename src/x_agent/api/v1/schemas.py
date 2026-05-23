from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from x_agent.domain.agent_message import AgentMessageRole
from x_agent.domain.agent_session import AgentSessionStatus
from x_agent.domain.nl2sql import SqlKnowledgeType


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


class AgentMessageSendResponse(BaseModel):
    messages: tuple[AgentMessageResponse, ...]


class Nl2SqlGenerateRequest(BaseModel):
    question: str = Field(min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class SqlRetrievalPlanStepResponse(BaseModel):
    query: str
    knowledge_types: tuple[SqlKnowledgeType, ...]
    reason: str


class SqlKnowledgeItemResponse(BaseModel):
    id: str
    type: SqlKnowledgeType
    name: str
    content: str
    metadata: dict[str, str]


class GeneratedSqlResponse(BaseModel):
    sql: str
    explanation: str
    assumptions: tuple[str, ...]


class SqlValidationResponse(BaseModel):
    is_valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    referenced_tables: tuple[str, ...]


class Nl2SqlGenerateResponse(BaseModel):
    question: str
    retrieval_plan: tuple[SqlRetrievalPlanStepResponse, ...]
    retrieved_context: tuple[SqlKnowledgeItemResponse, ...]
    generated_sql: GeneratedSqlResponse
    validation: SqlValidationResponse
