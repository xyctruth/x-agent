from x_agent.domain.nl2sql import SqlKnowledgeItem, SqlRetrievalPlanStep
from x_agent.infrastructure.composite_sql_knowledge_base import CompositeSqlKnowledgeBase


class FakeKnowledgeBase:
    def __init__(self, items: tuple[SqlKnowledgeItem, ...]) -> None:
        self._items = items

    def search(self, step: SqlRetrievalPlanStep) -> tuple[SqlKnowledgeItem, ...]:
        return self._items


def test_composite_sql_knowledge_base_merges_results_and_deduplicates_by_id() -> None:
    orders = SqlKnowledgeItem(
        id="table:orders",
        type="table",
        name="订单表",
        content="orders(id)",
        metadata={"table_name": "orders"},
    )
    payments = SqlKnowledgeItem(
        id="table:payments",
        type="table",
        name="支付表",
        content="payments(id)",
        metadata={"table_name": "payments"},
    )
    knowledge_base = CompositeSqlKnowledgeBase(
        knowledge_bases=(
            FakeKnowledgeBase((orders,)),
            FakeKnowledgeBase((orders, payments)),
        ),
    )

    items = knowledge_base.search(
        SqlRetrievalPlanStep(
            query="统计支付金额",
            knowledge_types=("table",),
            reason="检索表结构",
        ),
    )

    assert items == (orders, payments)
