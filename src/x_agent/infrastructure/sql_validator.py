import re

import sqlglot
from sqlglot import exp

from x_agent.domain.nl2sql import SqlValidationResult

DANGEROUS_SQL_PATTERN = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|merge|call|exec|grant|revoke)\b",
    re.IGNORECASE,
)


class SqlglotSqlValidator:
    def validate(
        self,
        sql: str,
        *,
        allowed_tables: tuple[str, ...],
    ) -> SqlValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        normalized_sql = sql.strip()

        if not normalized_sql:
            return SqlValidationResult(is_valid=False, errors=("SQL 不能为空。",))

        if self._has_multiple_statements(normalized_sql):
            errors.append("SQL 只能包含一条语句。")

        if DANGEROUS_SQL_PATTERN.search(normalized_sql):
            errors.append("SQL 包含禁止的写入或 DDL 关键字。")

        try:
            expressions = sqlglot.parse(normalized_sql)
        except sqlglot.errors.ParseError as exc:
            return SqlValidationResult(
                is_valid=False,
                errors=(*errors, f"SQL 语法解析失败: {exc}"),
            )

        if len(expressions) != 1 or expressions[0] is None:
            errors.append("SQL 只能解析为一条语句。")
            return SqlValidationResult(is_valid=False, errors=tuple(errors))

        expression = expressions[0]
        if not isinstance(expression, exp.Select | exp.Union):
            errors.append("SQL 只允许 SELECT 或 WITH SELECT 查询。")

        referenced_tables = tuple(
            dict.fromkeys(table.name for table in expression.find_all(exp.Table)),
        )
        unknown_tables = tuple(
            table for table in referenced_tables if allowed_tables and table not in allowed_tables
        )
        if unknown_tables:
            errors.append(f"SQL 引用了未检索到的表: {', '.join(unknown_tables)}。")

        if not referenced_tables:
            warnings.append("SQL 未引用任何物理表, 可能不是有效统计查询。")

        return SqlValidationResult(
            is_valid=not errors,
            errors=tuple(errors),
            warnings=tuple(warnings),
            referenced_tables=referenced_tables,
        )

    def _has_multiple_statements(self, sql: str) -> bool:
        sql_without_trailing_semicolon = sql[:-1] if sql.endswith(";") else sql
        return ";" in sql_without_trailing_semicolon
