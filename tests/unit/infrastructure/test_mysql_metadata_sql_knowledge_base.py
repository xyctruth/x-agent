from x_agent.domain.nl2sql import SqlRetrievalPlanStep
from x_agent.infrastructure.mysql_metadata_sql_knowledge_base import (
    MysqlColumnMetadata,
    MysqlConnectionConfig,
    MysqlForeignKeyMetadata,
    MysqlIndexMetadata,
    MysqlMetadataSqlKnowledgeBase,
    MysqlTableMetadata,
    PymysqlMysqlMetadataLoader,
)


class FakeMysqlMetadataLoader:
    def load_tables(self) -> tuple[MysqlTableMetadata, ...]:
        return (
            MysqlTableMetadata(
                name="fact_orders",
                comment="订单事实表, 记录订单主数据, 常用于订单数、GMV、客单价等统计",
                columns=(
                    MysqlColumnMetadata(
                        name="id",
                        data_type="bigint",
                        comment="订单主键",
                        is_nullable=False,
                        ordinal_position=1,
                    ),
                    MysqlColumnMetadata(
                        name="payable_amount",
                        data_type="decimal(12,2)",
                        comment="实际应付金额",
                        is_nullable=False,
                        ordinal_position=2,
                    ),
                ),
                primary_key=("id",),
                foreign_keys=(
                    MysqlForeignKeyMetadata(
                        column_name="user_id",
                        referenced_table_name="dim_users",
                        referenced_column_name="id",
                    ),
                ),
                indexes=(
                    MysqlIndexMetadata(
                        name="idx_fact_orders_created_at",
                        columns=("created_at",),
                        is_unique=False,
                    ),
                ),
            ),
            MysqlTableMetadata(
                name="risk_user_profiles",
                comment="用户风控画像表, 用于用户风险分层和黑名单分析",
                columns=(
                    MysqlColumnMetadata(
                        name="user_id",
                        data_type="bigint",
                        comment="用户 ID",
                        is_nullable=False,
                        ordinal_position=1,
                    ),
                    MysqlColumnMetadata(
                        name="risk_level",
                        data_type="varchar(32)",
                        comment="用户风险等级: low, medium, high",
                        is_nullable=False,
                        ordinal_position=2,
                    ),
                ),
                primary_key=("user_id",),
                foreign_keys=(),
                indexes=(),
            ),
        )


def test_mysql_metadata_knowledge_base_builds_table_items_from_loader() -> None:
    knowledge_base = MysqlMetadataSqlKnowledgeBase(loader=FakeMysqlMetadataLoader())

    items = knowledge_base.search(
        SqlRetrievalPlanStep(
            query="统计订单实际应付金额",
            knowledge_types=("table",),
            reason="检索表结构",
        ),
    )

    assert len(items) == 1
    assert items[0].id == "mysql_table:fact_orders"
    assert items[0].metadata == {"source": "mysql_metadata", "table_name": "fact_orders"}
    assert "fact_orders" in items[0].content
    assert "payable_amount decimal(12,2) NOT NULL COMMENT '实际应付金额'" in items[0].content
    assert "PRIMARY KEY (id)" in items[0].content
    assert "FOREIGN KEY (user_id) REFERENCES dim_users(id)" in items[0].content
    assert "INDEX idx_fact_orders_created_at (created_at)" in items[0].content


def test_mysql_metadata_knowledge_base_falls_back_to_all_tables_by_type() -> None:
    knowledge_base = MysqlMetadataSqlKnowledgeBase(loader=FakeMysqlMetadataLoader())

    items = knowledge_base.search(
        SqlRetrievalPlanStep(
            query="完全未知的问题",
            knowledge_types=("table",),
            reason="检索表结构",
        ),
    )

    assert {item.metadata["table_name"] for item in items} == {
        "fact_orders",
        "risk_user_profiles",
    }


def test_pymysql_metadata_loader_builds_table_metadata_from_information_schema_rows() -> None:
    loader = PymysqlMysqlMetadataLoader(
        config=MysqlConnectionConfig(
            host="127.0.0.1",
            port=3306,
            user="root",
            password=_test_mysql_password(),
            database="x_agent_mock_biz",
            connect_timeout_seconds=3.0,
        ),
    )

    tables = loader._build_tables(
        table_rows=(
            {
                "TABLE_NAME": "fact_payments",
                "TABLE_COMMENT": "支付事实表",
            },
        ),
        column_rows=(
            {
                "TABLE_NAME": "fact_payments",
                "COLUMN_NAME": "id",
                "COLUMN_TYPE": "bigint",
                "COLUMN_COMMENT": "支付主键",
                "IS_NULLABLE": "NO",
                "ORDINAL_POSITION": 1,
                "COLUMN_KEY": "PRI",
            },
            {
                "TABLE_NAME": "fact_payments",
                "COLUMN_NAME": "order_id",
                "COLUMN_TYPE": "bigint",
                "COLUMN_COMMENT": "订单 ID",
                "IS_NULLABLE": "NO",
                "ORDINAL_POSITION": 2,
                "COLUMN_KEY": "MUL",
            },
        ),
        foreign_key_rows=(
            {
                "TABLE_NAME": "fact_payments",
                "COLUMN_NAME": "order_id",
                "REFERENCED_TABLE_NAME": "fact_orders",
                "REFERENCED_COLUMN_NAME": "id",
            },
        ),
        index_rows=(
            {
                "TABLE_NAME": "fact_payments",
                "INDEX_NAME": "PRIMARY",
                "COLUMN_NAME": "id",
                "NON_UNIQUE": 0,
                "SEQ_IN_INDEX": 1,
            },
            {
                "TABLE_NAME": "fact_payments",
                "INDEX_NAME": "idx_fact_payments_order",
                "COLUMN_NAME": "order_id",
                "NON_UNIQUE": 1,
                "SEQ_IN_INDEX": 1,
            },
        ),
    )

    assert tables == (
        MysqlTableMetadata(
            name="fact_payments",
            comment="支付事实表",
            columns=(
                MysqlColumnMetadata(
                    name="id",
                    data_type="bigint",
                    comment="支付主键",
                    is_nullable=False,
                    ordinal_position=1,
                ),
                MysqlColumnMetadata(
                    name="order_id",
                    data_type="bigint",
                    comment="订单 ID",
                    is_nullable=False,
                    ordinal_position=2,
                ),
            ),
            primary_key=("id",),
            foreign_keys=(
                MysqlForeignKeyMetadata(
                    column_name="order_id",
                    referenced_table_name="fact_orders",
                    referenced_column_name="id",
                ),
            ),
            indexes=(
                MysqlIndexMetadata(
                    name="idx_fact_payments_order",
                    columns=("order_id",),
                    is_unique=False,
                ),
            ),
        ),
    )


def _test_mysql_password() -> str:
    return "root"
