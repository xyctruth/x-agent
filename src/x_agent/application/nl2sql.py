from dataclasses import dataclass, field
from typing import Protocol

from x_agent.domain.nl2sql import (
    GeneratedSql,
    Nl2SqlGenerationResult,
    SqlKnowledgeItem,
    SqlRetrievalPlanStep,
    SqlValidationResult,
)


class SqlKnowledgeBase(Protocol):
    def search(self, step: SqlRetrievalPlanStep) -> tuple[SqlKnowledgeItem, ...]: ...


class SqlValidator(Protocol):
    def validate(
        self,
        sql: str,
        *,
        allowed_tables: tuple[str, ...],
    ) -> SqlValidationResult: ...


class Nl2SqlAgent(Protocol):
    def plan_retrieval(self, question: str) -> tuple[SqlRetrievalPlanStep, ...]: ...

    def generate_sql(
        self,
        *,
        question: str,
        context: tuple[SqlKnowledgeItem, ...],
    ) -> GeneratedSql: ...


@dataclass(frozen=True, slots=True)
class GenerateSqlCommand:
    question: str
    metadata: dict[str, str] = field(default_factory=dict)


class Nl2SqlService:
    def __init__(
        self,
        *,
        agent: Nl2SqlAgent,
        knowledge_base: SqlKnowledgeBase,
        validator: SqlValidator,
    ) -> None:
        self._agent = agent
        self._knowledge_base = knowledge_base
        self._validator = validator

    def generate(self, command: GenerateSqlCommand) -> Nl2SqlGenerationResult:
        retrieval_plan = self._agent.plan_retrieval(command.question)
        retrieved_context = self._retrieve_context(retrieval_plan)
        generated_sql = self._agent.generate_sql(
            question=command.question,
            context=retrieved_context,
        )
        validation = self._validator.validate(
            generated_sql.sql,
            allowed_tables=self._allowed_tables(retrieved_context),
        )
        return Nl2SqlGenerationResult(
            question=command.question,
            retrieval_plan=retrieval_plan,
            retrieved_context=retrieved_context,
            generated_sql=generated_sql,
            validation=validation,
        )

    def _retrieve_context(
        self,
        retrieval_plan: tuple[SqlRetrievalPlanStep, ...],
    ) -> tuple[SqlKnowledgeItem, ...]:
        items_by_id: dict[str, SqlKnowledgeItem] = {}
        for step in retrieval_plan:
            for item in self._knowledge_base.search(step):
                items_by_id.setdefault(item.id, item)
        return tuple(items_by_id.values())

    def _allowed_tables(self, context: tuple[SqlKnowledgeItem, ...]) -> tuple[str, ...]:
        table_names = [
            item.metadata["table_name"]
            for item in context
            if item.type == "table" and "table_name" in item.metadata
        ]
        return tuple(dict.fromkeys(table_names))
