#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-root}"
MYSQL_DATABASE="${MYSQL_DATABASE:-x_agent_mock_biz}"

MYSQL_ARGS=(
  "-h${MYSQL_HOST}"
  "-P${MYSQL_PORT}"
  "-u${MYSQL_USER}"
  "--default-character-set=utf8mb4"
)

echo "Initializing MySQL mock business database: ${MYSQL_DATABASE}"
MYSQL_PWD="${MYSQL_PASSWORD}" mysql "${MYSQL_ARGS[@]}" < "${ROOT_DIR}/database/mock_mysql/001_schema.sql"
MYSQL_PWD="${MYSQL_PASSWORD}" mysql "${MYSQL_ARGS[@]}" < "${ROOT_DIR}/database/mock_mysql/002_seed.sql"

echo "Initialized ${MYSQL_DATABASE}. Table counts:"
MYSQL_PWD="${MYSQL_PASSWORD}" mysql "${MYSQL_ARGS[@]}" "${MYSQL_DATABASE}" <<'SQL'
SELECT 'dim_regions' AS table_name, COUNT(*) AS row_count FROM dim_regions
UNION ALL SELECT 'dim_users', COUNT(*) FROM dim_users
UNION ALL SELECT 'dim_merchants', COUNT(*) FROM dim_merchants
UNION ALL SELECT 'dim_categories', COUNT(*) FROM dim_categories
UNION ALL SELECT 'dim_products', COUNT(*) FROM dim_products
UNION ALL SELECT 'fact_orders', COUNT(*) FROM fact_orders
UNION ALL SELECT 'fact_order_items', COUNT(*) FROM fact_order_items
UNION ALL SELECT 'fact_payments', COUNT(*) FROM fact_payments
UNION ALL SELECT 'fact_refunds', COUNT(*) FROM fact_refunds
UNION ALL SELECT 'fact_user_events', COUNT(*) FROM fact_user_events
UNION ALL SELECT 'risk_user_profiles', COUNT(*) FROM risk_user_profiles
UNION ALL SELECT 'risk_merchant_profiles', COUNT(*) FROM risk_merchant_profiles
UNION ALL SELECT 'risk_rules', COUNT(*) FROM risk_rules
UNION ALL SELECT 'risk_rule_hits', COUNT(*) FROM risk_rule_hits
UNION ALL SELECT 'risk_cases', COUNT(*) FROM risk_cases
UNION ALL SELECT 'risk_case_actions', COUNT(*) FROM risk_case_actions;
SQL
