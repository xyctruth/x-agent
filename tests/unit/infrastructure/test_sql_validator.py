from x_agent.infrastructure.sql_validator import SqlglotSqlValidator


def test_sql_validator_allows_select_query_for_known_tables() -> None:
    validator = SqlglotSqlValidator()

    result = validator.validate(
        "SELECT COUNT(*) AS order_count FROM orders",
        allowed_tables=("orders",),
    )

    assert result.is_valid is True
    assert result.errors == ()
    assert result.referenced_tables == ("orders",)


def test_sql_validator_rejects_write_query() -> None:
    validator = SqlglotSqlValidator()

    result = validator.validate(
        "DELETE FROM orders",
        allowed_tables=("orders",),
    )

    assert result.is_valid is False
    assert "SQL 包含禁止的写入或 DDL 关键字。" in result.errors


def test_sql_validator_rejects_unknown_tables() -> None:
    validator = SqlglotSqlValidator()

    result = validator.validate(
        "SELECT COUNT(*) FROM secret_orders",
        allowed_tables=("orders",),
    )

    assert result.is_valid is False
    assert result.errors == ("SQL 引用了未检索到的表: secret_orders。",)


def test_sql_validator_rejects_multiple_statements() -> None:
    validator = SqlglotSqlValidator()

    result = validator.validate(
        "SELECT COUNT(*) FROM orders; SELECT COUNT(*) FROM users",
        allowed_tables=("orders", "users"),
    )

    assert result.is_valid is False
    assert "SQL 只能包含一条语句。" in result.errors
