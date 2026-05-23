from collections.abc import Iterator

from x_agent.agent.nl2sql_agent import AgenticRagNl2SqlAgent
from x_agent.application.llm import LLMCompletion, LLMCompletionChunk, LLMMessage
from x_agent.domain.nl2sql import SqlKnowledgeItem


class FakeLLMProvider:
    def __init__(self, content: str) -> None:
        self.content = content
        self.messages: tuple[LLMMessage, ...] = ()

    def complete(self, messages: tuple[LLMMessage, ...]) -> LLMCompletion:
        self.messages = messages
        return LLMCompletion(
            content=self.content,
            provider="fake",
            model="fake-model",
        )

    def stream_complete(
        self,
        messages: tuple[LLMMessage, ...],
    ) -> Iterator[LLMCompletionChunk]:
        return iter(())


def test_nl2sql_agent_plans_retrieval_steps() -> None:
    agent = AgenticRagNl2SqlAgent()

    plan = agent.plan_retrieval("统计最近 7 天订单数和支付金额")

    assert [step.knowledge_types for step in plan] == [
        ("term", "metric"),
        ("table",),
        ("example",),
    ]


def test_nl2sql_agent_generates_deterministic_order_payment_sql() -> None:
    agent = AgenticRagNl2SqlAgent()

    generated = agent.generate_sql(
        question="统计最近 7 天订单数和支付金额",
        context=(),
    )

    assert "COUNT(DISTINCT o.id)" in generated.sql
    assert "LEFT JOIN payments" in generated.sql
    assert generated.assumptions


def test_nl2sql_agent_generates_sql_with_llm_provider() -> None:
    provider = FakeLLMProvider(
        content=(
            '{"sql":"SELECT COUNT(*) AS order_count FROM orders",'
            '"explanation":"统计订单数","assumptions":["使用 orders 表"]}'
        ),
    )
    agent = AgenticRagNl2SqlAgent(llm_provider=provider)

    generated = agent.generate_sql(
        question="统计订单数",
        context=(
            SqlKnowledgeItem(
                id="table:orders",
                type="table",
                name="订单表",
                content="orders(id)",
                metadata={"table_name": "orders"},
            ),
        ),
    )

    assert provider.messages[0].role == "system"
    assert "统计订单数" in provider.messages[1].content
    assert generated.sql == "SELECT COUNT(*) AS order_count FROM orders"
    assert generated.assumptions == ("使用 orders 表",)
