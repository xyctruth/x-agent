import json
from collections.abc import Mapping

from x_agent.application.llm import LLMMessage, LLMProvider
from x_agent.domain.nl2sql import GeneratedSql, SqlKnowledgeItem, SqlRetrievalPlanStep


class Nl2SqlGenerationError(Exception):
    pass


class AgenticRagNl2SqlAgent:
    def __init__(self, *, llm_provider: LLMProvider | None = None) -> None:
        self._llm_provider = llm_provider

    def plan_retrieval(self, question: str) -> tuple[SqlRetrievalPlanStep, ...]:
        normalized_question = question.strip()
        return (
            SqlRetrievalPlanStep(
                query=normalized_question,
                knowledge_types=("term", "metric"),
                reason="识别用户问题中的业务术语和统计指标。",
            ),
            SqlRetrievalPlanStep(
                query=normalized_question,
                knowledge_types=("table",),
                reason="检索可能参与统计查询的事实表和维表结构。",
            ),
            SqlRetrievalPlanStep(
                query=normalized_question,
                knowledge_types=("example",),
                reason="参考历史相似查询样例, 提升 SQL 结构质量。",
            ),
        )

    def generate_sql(
        self,
        *,
        question: str,
        context: tuple[SqlKnowledgeItem, ...],
    ) -> GeneratedSql:
        if self._llm_provider is None:
            return self._generate_deterministic_sql(question=question, context=context)
        return self._generate_with_llm(question=question, context=context)

    def _generate_with_llm(
        self,
        *,
        question: str,
        context: tuple[SqlKnowledgeItem, ...],
    ) -> GeneratedSql:
        llm_provider = self._llm_provider
        if llm_provider is None:
            raise Nl2SqlGenerationError("LLM provider is required")

        completion = llm_provider.complete(
            (
                LLMMessage(
                    role="system",
                    content=(
                        "你是生产级 NL2SQL Agent。你只能基于给定知识库上下文生成只读统计 SQL。"
                        "必须返回严格 JSON, 字段为 sql、explanation、assumptions。"
                        "不要返回 Markdown, 不要返回代码块。"
                    ),
                ),
                LLMMessage(
                    role="user",
                    content=self._build_prompt(question=question, context=context),
                ),
            ),
        )
        return self._parse_generated_sql(completion.content)

    def _generate_deterministic_sql(
        self,
        *,
        question: str,
        context: tuple[SqlKnowledgeItem, ...],
    ) -> GeneratedSql:
        if "支付" in question or "金额" in question:
            return GeneratedSql(
                sql=(
                    "SELECT DATE(o.created_at) AS stat_date, "
                    "COUNT(DISTINCT o.id) AS order_count, "
                    "COALESCE(SUM(p.amount), 0) AS paid_amount "
                    "FROM orders o "
                    "LEFT JOIN payments p ON p.order_id = o.id AND p.status = 'paid' "
                    "WHERE o.created_at >= CURRENT_DATE - INTERVAL '7' DAY "
                    "GROUP BY DATE(o.created_at) "
                    "ORDER BY stat_date"
                ),
                explanation="按订单创建日期统计最近 7 天订单数, 并关联支付表汇总已支付金额。",
                assumptions=("最近 7 天按订单创建时间过滤。", "支付金额只统计状态为 paid 的记录。"),
            )

        if "用户" in question:
            return GeneratedSql(
                sql=(
                    "SELECT u.risk_level, COUNT(*) AS user_count "
                    "FROM users u "
                    "GROUP BY u.risk_level "
                    "ORDER BY user_count DESC"
                ),
                explanation="按用户风险等级聚合用户数量。",
                assumptions=("用户风险等级来自 users.risk_level 字段。",),
            )

        table_names = {
            item.metadata["table_name"]
            for item in context
            if item.type == "table" and "table_name" in item.metadata
        }
        table_name = "users" if "users" in table_names and "orders" not in table_names else "orders"
        sql = (
            "SELECT COUNT(*) AS row_count FROM users"
            if table_name == "users"
            else "SELECT COUNT(*) AS row_count FROM orders"
        )
        return GeneratedSql(
            sql=sql,
            explanation=f"未识别到明确指标时, 默认统计 {table_name} 表记录数。",
            assumptions=("这是本地 deterministic 生成器的兜底 SQL。",),
        )

    def _build_prompt(self, *, question: str, context: tuple[SqlKnowledgeItem, ...]) -> str:
        context_lines = [
            {
                "type": item.type,
                "name": item.name,
                "content": item.content,
                "metadata": item.metadata,
            }
            for item in context
        ]
        return json.dumps(
            {
                "question": question,
                "context": context_lines,
                "requirements": [
                    "只生成 SELECT 或 WITH SELECT 查询。",
                    "优先使用知识库中存在的表和字段。",
                    "统计查询需要给出清晰别名。",
                    "返回 JSON: sql, explanation, assumptions。",
                ],
            },
            ensure_ascii=False,
        )

    def _parse_generated_sql(self, content: str) -> GeneratedSql:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise Nl2SqlGenerationError("LLM did not return valid JSON") from exc

        if not isinstance(payload, Mapping):
            raise Nl2SqlGenerationError("LLM JSON response must be an object")

        sql = payload.get("sql")
        explanation = payload.get("explanation")
        assumptions = payload.get("assumptions", ())
        if not isinstance(sql, str) or not sql.strip():
            raise Nl2SqlGenerationError("LLM JSON response missing sql")
        if not isinstance(explanation, str):
            raise Nl2SqlGenerationError("LLM JSON response missing explanation")
        return GeneratedSql(
            sql=sql.strip(),
            explanation=explanation,
            assumptions=self._parse_assumptions(assumptions),
        )

    def _parse_assumptions(self, assumptions: object) -> tuple[str, ...]:
        if assumptions is None:
            return ()
        if isinstance(assumptions, list):
            return tuple(item for item in assumptions if isinstance(item, str))
        if isinstance(assumptions, str):
            return (assumptions,)
        raise Nl2SqlGenerationError("LLM JSON response assumptions must be a list or string")
