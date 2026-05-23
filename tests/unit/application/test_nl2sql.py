from x_agent.application.nl2sql import GenerateSqlCommand, Nl2SqlService
from x_agent.domain.nl2sql import (
    GeneratedSql,
    SqlKnowledgeItem,
    SqlRetrievalPlanStep,
    SqlValidationResult,
)


class FakeNl2SqlAgent:
    def plan_retrieval(self, question: str) -> tuple[SqlRetrievalPlanStep, ...]:
        return (
            SqlRetrievalPlanStep(
                query=question,
                knowledge_types=("table",),
                reason="检索表结构",
            ),
        )

    def generate_sql(
        self,
        *,
        question: str,
        context: tuple[SqlKnowledgeItem, ...],
    ) -> GeneratedSql:
        return GeneratedSql(
            sql="SELECT COUNT(*) AS order_count FROM orders",
            explanation="统计订单数",
        )


class FakeKnowledgeBase:
    def search(self, step: SqlRetrievalPlanStep) -> tuple[SqlKnowledgeItem, ...]:
        return (
            SqlKnowledgeItem(
                id="table:orders",
                type="table",
                name="订单表",
                content="orders(id, created_at)",
                metadata={"table_name": "orders"},
            ),
        )


class FakeSqlValidator:
    def validate(
        self,
        sql: str,
        *,
        allowed_tables: tuple[str, ...],
    ) -> SqlValidationResult:
        return SqlValidationResult(
            is_valid=True,
            referenced_tables=allowed_tables,
        )


def test_nl2sql_service_orchestrates_retrieval_generation_and_validation() -> None:
    service = Nl2SqlService(
        agent=FakeNl2SqlAgent(),
        knowledge_base=FakeKnowledgeBase(),
        validator=FakeSqlValidator(),
    )

    result = service.generate(GenerateSqlCommand(question="统计订单数"))

    assert result.question == "统计订单数"
    assert result.retrieval_plan[0].reason == "检索表结构"
    assert result.retrieved_context[0].metadata == {"table_name": "orders"}
    assert result.generated_sql.sql == "SELECT COUNT(*) AS order_count FROM orders"
    assert result.validation.is_valid is True
    assert result.validation.referenced_tables == ("orders",)
