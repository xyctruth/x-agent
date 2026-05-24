# Mock MySQL 业务库

该目录用于初始化本地 MySQL 8.0 mock 业务库，供 NL2SQL、SQL 校验、后续只读执行和数据分析能力测试使用。

默认库名：

```text
x_agent_mock_biz
```

## 表范围

当前包含电商、支付和风控混合业务域：

- `dim_regions`：区域维表。
- `dim_users`：用户维表。
- `dim_merchants`：商户维表。
- `dim_categories`：商品类目维表。
- `dim_products`：商品维表。
- `fact_orders`：订单事实表。
- `fact_order_items`：订单明细事实表。
- `fact_payments`：支付事实表。
- `fact_refunds`：退款事实表。
- `fact_user_events`：用户行为事实表。
- `risk_user_profiles`：用户风控画像表。
- `risk_merchant_profiles`：商户风控画像表。
- `risk_rules`：风控规则表。
- `risk_rule_hits`：风控规则命中事实表。
- `risk_cases`：风控案件表。
- `risk_case_actions`：风控案件处置动作表。

## 初始化

默认连接本地 Docker MySQL：

```bash
bash scripts/init_mock_mysql.sh
```

默认参数：

```text
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=x_agent_mock_biz
```

可以通过环境变量覆盖：

```bash
MYSQL_HOST=127.0.0.1 MYSQL_PORT=3306 MYSQL_USER=root MYSQL_PASSWORD=root bash scripts/init_mock_mysql.sh
```

## 验证 SQL

```sql
SELECT COUNT(*) AS order_count FROM fact_orders;

SELECT
  DATE(created_at) AS stat_date,
  COUNT(*) AS order_count,
  SUM(payable_amount) AS payable_amount
FROM fact_orders
GROUP BY DATE(created_at)
ORDER BY stat_date;

SELECT
  rup.risk_level,
  COUNT(DISTINCT o.id) AS order_count,
  SUM(p.amount) AS paid_amount
FROM risk_user_profiles rup
JOIN fact_orders o ON o.user_id = rup.user_id
LEFT JOIN fact_payments p ON p.order_id = o.id AND p.payment_status = 'paid'
GROUP BY rup.risk_level;
```

## NL2SQL metadata 检索

后端服务可以通过以下配置让 NL2SQL 从该库读取真实 metadata：

```bash
export X_AGENT_NL2SQL_KNOWLEDGE_SOURCE=mysql
export X_AGENT_MYSQL_HOST=127.0.0.1
export X_AGENT_MYSQL_PORT=3306
export X_AGENT_MYSQL_USER=root
export X_AGENT_MYSQL_PASSWORD=root
export X_AGENT_MYSQL_DATABASE=x_agent_mock_biz
```

服务会读取 `information_schema.TABLES`、`COLUMNS`、`KEY_COLUMN_USAGE` 和 `STATISTICS`，生成可被 Agentic RAG 检索的表结构上下文。
