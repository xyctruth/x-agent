from x_agent.domain.nl2sql import SqlRetrievalPlanStep
from x_agent.infrastructure.in_memory_sql_knowledge_base import InMemorySqlKnowledgeBase


def test_in_memory_sql_knowledge_base_searches_relevant_tables() -> None:
    knowledge_base = InMemorySqlKnowledgeBase()

    items = knowledge_base.search(
        SqlRetrievalPlanStep(
            query="统计支付金额",
            knowledge_types=("table",),
            reason="检索表结构",
        ),
    )

    table_names = {item.metadata.get("table_name") for item in items}
    assert "payments" in table_names


def test_in_memory_sql_knowledge_base_falls_back_by_type() -> None:
    knowledge_base = InMemorySqlKnowledgeBase()

    items = knowledge_base.search(
        SqlRetrievalPlanStep(
            query="完全未知的问题",
            knowledge_types=("metric",),
            reason="检索指标",
        ),
    )

    assert {item.type for item in items} == {"metric"}
