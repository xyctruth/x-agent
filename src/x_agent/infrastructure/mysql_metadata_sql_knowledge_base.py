from dataclasses import dataclass
from importlib import import_module
from typing import Any, Protocol, cast

from x_agent.domain.nl2sql import SqlKnowledgeItem, SqlRetrievalPlanStep


@dataclass(frozen=True, slots=True)
class MysqlConnectionConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    connect_timeout_seconds: float


@dataclass(frozen=True, slots=True)
class MysqlColumnMetadata:
    name: str
    data_type: str
    comment: str
    is_nullable: bool
    ordinal_position: int


@dataclass(frozen=True, slots=True)
class MysqlForeignKeyMetadata:
    column_name: str
    referenced_table_name: str
    referenced_column_name: str


@dataclass(frozen=True, slots=True)
class MysqlIndexMetadata:
    name: str
    columns: tuple[str, ...]
    is_unique: bool


@dataclass(frozen=True, slots=True)
class MysqlTableMetadata:
    name: str
    comment: str
    columns: tuple[MysqlColumnMetadata, ...]
    primary_key: tuple[str, ...]
    foreign_keys: tuple[MysqlForeignKeyMetadata, ...]
    indexes: tuple[MysqlIndexMetadata, ...]


class MysqlMetadataLoader(Protocol):
    def load_tables(self) -> tuple[MysqlTableMetadata, ...]: ...


class PymysqlMysqlMetadataLoader:
    def __init__(self, *, config: MysqlConnectionConfig) -> None:
        self._config = config

    def load_tables(self) -> tuple[MysqlTableMetadata, ...]:
        connection = self._connect()
        try:
            table_rows = self._fetch_all(
                connection,
                """
                SELECT TABLE_NAME, TABLE_COMMENT
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
                """,
                (self._config.database,),
            )
            column_rows = self._fetch_all(
                connection,
                """
                SELECT
                  TABLE_NAME,
                  COLUMN_NAME,
                  COLUMN_TYPE,
                  COLUMN_COMMENT,
                  IS_NULLABLE,
                  ORDINAL_POSITION,
                  COLUMN_KEY
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME, ORDINAL_POSITION
                """,
                (self._config.database,),
            )
            foreign_key_rows = self._fetch_all(
                connection,
                """
                SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s
                  AND REFERENCED_TABLE_NAME IS NOT NULL
                ORDER BY TABLE_NAME, CONSTRAINT_NAME, ORDINAL_POSITION
                """,
                (self._config.database,),
            )
            index_rows = self._fetch_all(
                connection,
                """
                SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME, NON_UNIQUE, SEQ_IN_INDEX
                FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX
                """,
                (self._config.database,),
            )
        finally:
            connection.close()

        return self._build_tables(
            table_rows=table_rows,
            column_rows=column_rows,
            foreign_key_rows=foreign_key_rows,
            index_rows=index_rows,
        )

    def _connect(self) -> Any:
        pymysql = import_module("pymysql")
        return pymysql.connect(
            host=self._config.host,
            port=self._config.port,
            user=self._config.user,
            password=self._config.password,
            database=self._config.database,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=self._config.connect_timeout_seconds,
        )

    def _fetch_all(
        self,
        connection: Any,
        sql: str,
        params: tuple[str, ...],
    ) -> tuple[dict[str, Any], ...]:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return tuple(cast("dict[str, Any]", row) for row in cursor.fetchall())

    def _build_tables(
        self,
        *,
        table_rows: tuple[dict[str, Any], ...],
        column_rows: tuple[dict[str, Any], ...],
        foreign_key_rows: tuple[dict[str, Any], ...],
        index_rows: tuple[dict[str, Any], ...],
    ) -> tuple[MysqlTableMetadata, ...]:
        columns_by_table: dict[str, list[MysqlColumnMetadata]] = {}
        primary_keys_by_table: dict[str, list[str]] = {}
        for row in column_rows:
            table_name = str(row["TABLE_NAME"])
            column_name = str(row["COLUMN_NAME"])
            columns_by_table.setdefault(table_name, []).append(
                MysqlColumnMetadata(
                    name=column_name,
                    data_type=str(row["COLUMN_TYPE"]),
                    comment=str(row["COLUMN_COMMENT"] or ""),
                    is_nullable=str(row["IS_NULLABLE"]).upper() == "YES",
                    ordinal_position=int(row["ORDINAL_POSITION"]),
                ),
            )
            if row.get("COLUMN_KEY") == "PRI":
                primary_keys_by_table.setdefault(table_name, []).append(column_name)

        foreign_keys_by_table: dict[str, list[MysqlForeignKeyMetadata]] = {}
        for row in foreign_key_rows:
            table_name = str(row["TABLE_NAME"])
            foreign_keys_by_table.setdefault(table_name, []).append(
                MysqlForeignKeyMetadata(
                    column_name=str(row["COLUMN_NAME"]),
                    referenced_table_name=str(row["REFERENCED_TABLE_NAME"]),
                    referenced_column_name=str(row["REFERENCED_COLUMN_NAME"]),
                ),
            )

        indexes_by_table = self._build_indexes_by_table(index_rows)
        return tuple(
            MysqlTableMetadata(
                name=str(row["TABLE_NAME"]),
                comment=str(row["TABLE_COMMENT"] or ""),
                columns=tuple(columns_by_table.get(str(row["TABLE_NAME"]), ())),
                primary_key=tuple(primary_keys_by_table.get(str(row["TABLE_NAME"]), ())),
                foreign_keys=tuple(foreign_keys_by_table.get(str(row["TABLE_NAME"]), ())),
                indexes=tuple(indexes_by_table.get(str(row["TABLE_NAME"]), ())),
            )
            for row in table_rows
        )

    def _build_indexes_by_table(
        self,
        index_rows: tuple[dict[str, Any], ...],
    ) -> dict[str, list[MysqlIndexMetadata]]:
        grouped_columns: dict[tuple[str, str], list[str]] = {}
        unique_flags: dict[tuple[str, str], bool] = {}
        for row in index_rows:
            table_name = str(row["TABLE_NAME"])
            index_name = str(row["INDEX_NAME"])
            key = (table_name, index_name)
            grouped_columns.setdefault(key, []).append(str(row["COLUMN_NAME"]))
            unique_flags[key] = int(row["NON_UNIQUE"]) == 0

        indexes_by_table: dict[str, list[MysqlIndexMetadata]] = {}
        for (table_name, index_name), columns in grouped_columns.items():
            if index_name == "PRIMARY":
                continue
            indexes_by_table.setdefault(table_name, []).append(
                MysqlIndexMetadata(
                    name=index_name,
                    columns=tuple(columns),
                    is_unique=unique_flags[(table_name, index_name)],
                ),
            )
        return indexes_by_table


class MysqlMetadataSqlKnowledgeBase:
    def __init__(self, *, loader: MysqlMetadataLoader) -> None:
        self._loader = loader
        self._items: tuple[SqlKnowledgeItem, ...] | None = None

    def search(self, step: SqlRetrievalPlanStep) -> tuple[SqlKnowledgeItem, ...]:
        if "table" not in step.knowledge_types:
            return ()

        query_tokens = self._tokenize(step.query)
        matched_items = [
            item
            for item in self._load_items()
            if any(token in self._searchable_text(item) for token in query_tokens)
        ]
        return tuple(matched_items) if matched_items else self._load_items()

    def list_items(self) -> tuple[SqlKnowledgeItem, ...]:
        return self._load_items()

    def _load_items(self) -> tuple[SqlKnowledgeItem, ...]:
        if self._items is None:
            self._items = tuple(self._table_to_item(table) for table in self._loader.load_tables())
        return self._items

    def _table_to_item(self, table: MysqlTableMetadata) -> SqlKnowledgeItem:
        lines = [f"{table.name}: {table.comment}".strip()]
        lines.extend(self._column_lines(table.columns))
        if table.primary_key:
            lines.append(f"PRIMARY KEY ({', '.join(table.primary_key)})")
        lines.extend(
            f"FOREIGN KEY ({foreign_key.column_name}) "
            f"REFERENCES {foreign_key.referenced_table_name}"
            f"({foreign_key.referenced_column_name})"
            for foreign_key in table.foreign_keys
        )
        lines.extend(
            f"{'UNIQUE ' if index.is_unique else ''}INDEX {index.name} ({', '.join(index.columns)})"
            for index in table.indexes
        )
        return SqlKnowledgeItem(
            id=f"mysql_table:{table.name}",
            type="table",
            name=table.comment or table.name,
            content="\n".join(lines),
            metadata={"source": "mysql_metadata", "table_name": table.name},
        )

    def _column_lines(self, columns: tuple[MysqlColumnMetadata, ...]) -> tuple[str, ...]:
        return tuple(
            (
                f"- {column.name} {column.data_type} "
                f"{'NULL' if column.is_nullable else 'NOT NULL'}"
                f"{self._comment_suffix(column.comment)}"
            )
            for column in sorted(columns, key=lambda item: item.ordinal_position)
        )

    def _comment_suffix(self, comment: str) -> str:
        return f" COMMENT '{comment}'" if comment else ""

    def _searchable_text(self, item: SqlKnowledgeItem) -> str:
        return " ".join((item.name, item.content, " ".join(item.metadata.values()))).lower()

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
                "商户",
                "商品",
                "退款",
                "城市",
                "区域",
                "order",
                "payment",
                "user",
                "risk",
                "merchant",
                "refund",
            )
            if token in normalized_query
        ]
        return tuple(tokens) or (normalized_query,)
