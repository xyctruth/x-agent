from dataclasses import dataclass, field
from typing import Literal

SqlKnowledgeType = Literal["table", "metric", "term", "example"]


@dataclass(frozen=True, slots=True)
class SqlKnowledgeItem:
    id: str
    type: SqlKnowledgeType
    name: str
    content: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SqlRetrievalPlanStep:
    query: str
    knowledge_types: tuple[SqlKnowledgeType, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class GeneratedSql:
    sql: str
    explanation: str
    assumptions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SqlValidationResult:
    is_valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    referenced_tables: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Nl2SqlGenerationResult:
    question: str
    retrieval_plan: tuple[SqlRetrievalPlanStep, ...]
    retrieved_context: tuple[SqlKnowledgeItem, ...]
    generated_sql: GeneratedSql
    validation: SqlValidationResult
