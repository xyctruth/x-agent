from x_agent.domain.nl2sql import SqlKnowledgeItem, SqlRetrievalPlanStep


class InMemorySqlKnowledgeBase:
    def __init__(self, *, items: tuple[SqlKnowledgeItem, ...] | None = None) -> None:
        self._items = items or default_sql_knowledge_items()

    def search(self, step: SqlRetrievalPlanStep) -> tuple[SqlKnowledgeItem, ...]:
        query_tokens = self._tokenize(step.query)
        matched_items: list[SqlKnowledgeItem] = []
        for item in self._items:
            if item.type not in step.knowledge_types:
                continue
            searchable_text = " ".join(
                (
                    item.name,
                    item.content,
                    " ".join(item.metadata.values()),
                ),
            ).lower()
            if any(token in searchable_text for token in query_tokens):
                matched_items.append(item)

        if matched_items:
            return tuple(matched_items)

        return tuple(item for item in self._items if item.type in step.knowledge_types)

    def list_items(self) -> tuple[SqlKnowledgeItem, ...]:
        return self._items

    def _tokenize(self, query: str) -> tuple[str, ...]:
        normalized_query = query.lower()
        tokens = [
            token
            for token in (
                "订单",
                "支付",
                "金额",
                "用户",
                "风控",
                "风险",
                "商品",
                "最近",
                "每天",
                "统计",
                "order",
                "payment",
                "user",
                "risk",
            )
            if token in normalized_query
        ]
        return tuple(tokens) or (normalized_query,)


def default_sql_knowledge_items() -> tuple[SqlKnowledgeItem, ...]:
    return (
        SqlKnowledgeItem(
            id="table:fact_orders",
            type="table",
            name="订单表",
            content=(
                "fact_orders(id, user_id, merchant_id, region_id, order_status, "
                "total_amount, discount_amount, payable_amount, created_at, paid_at)。"
                "记录订单主数据, created_at 为下单时间, payable_amount 为实际应付金额。"
            ),
            metadata={"table_name": "fact_orders", "primary_key": "id"},
        ),
        SqlKnowledgeItem(
            id="table:fact_payments",
            type="table",
            name="支付表",
            content=(
                "fact_payments(id, order_id, user_id, channel, payment_status, amount, paid_at)。"
                "记录订单支付流水, payment_status='paid' 表示支付成功, amount 为实际支付金额。"
            ),
            metadata={"table_name": "fact_payments", "primary_key": "id"},
        ),
        SqlKnowledgeItem(
            id="table:dim_users",
            type="table",
            name="用户表",
            content=(
                "dim_users(id, user_no, region_id, gender, age, registered_at, status)。"
                "记录用户基础信息, 可通过 region_id 关联 dim_regions.id。"
            ),
            metadata={"table_name": "dim_users", "primary_key": "id"},
        ),
        SqlKnowledgeItem(
            id="table:fact_order_items",
            type="table",
            name="订单明细表",
            content=(
                "fact_order_items(id, order_id, product_id, quantity, item_amount)。"
                "记录订单商品明细, 可通过 order_id 关联 fact_orders.id。"
            ),
            metadata={"table_name": "fact_order_items", "primary_key": "id"},
        ),
        SqlKnowledgeItem(
            id="table:risk_user_profiles",
            type="table",
            name="用户风控画像表",
            content=(
                "risk_user_profiles(user_id, risk_level, risk_score, is_blacklisted, "
                "last_evaluated_at)。记录用户风险分层, 可通过 user_id 关联 dim_users.id。"
            ),
            metadata={"table_name": "risk_user_profiles", "primary_key": "user_id"},
        ),
        SqlKnowledgeItem(
            id="table:dim_regions",
            type="table",
            name="区域维表",
            content=(
                "dim_regions(id, region_code, region_name, province, city, tier)。"
                "支持城市维度统计。"
            ),
            metadata={"table_name": "dim_regions", "primary_key": "id"},
        ),
        SqlKnowledgeItem(
            id="metric:order_count",
            type="metric",
            name="订单数",
            content=(
                "订单数使用 COUNT(DISTINCT fact_orders.id) 计算, "
                "统计周期通常基于 fact_orders.created_at。"
            ),
        ),
        SqlKnowledgeItem(
            id="metric:paid_amount",
            type="metric",
            name="支付金额",
            content=(
                "支付金额使用 SUM(fact_payments.amount) 计算, "
                "仅统计 fact_payments.payment_status='paid' 的支付记录。"
            ),
        ),
        SqlKnowledgeItem(
            id="term:last_7_days",
            type="term",
            name="最近 7 天",
            content="最近 7 天表示 CURRENT_DATE - INTERVAL '7' DAY 至当前日期。",
        ),
        SqlKnowledgeItem(
            id="term:risk_level",
            type="term",
            name="风险等级",
            content=(
                "用户风险等级来自 risk_user_profiles.risk_level, 常见取值为 low、medium、high。"
            ),
        ),
        SqlKnowledgeItem(
            id="example:daily_order_paid_amount",
            type="example",
            name="按天统计订单数和支付金额",
            content=(
                "SELECT DATE(o.created_at) AS stat_date, "
                "COUNT(DISTINCT o.id) AS order_count, "
                "COALESCE(SUM(p.amount), 0) AS paid_amount "
                "FROM fact_orders o "
                "LEFT JOIN fact_payments p ON p.order_id = o.id "
                "AND p.payment_status = 'paid' "
                "GROUP BY DATE(o.created_at)"
            ),
        ),
    )
