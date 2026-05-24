import pytest

from x_agent.agent.qwen_agent import QwenAgent
from x_agent.agent.simple_agent import SimpleAgent
from x_agent.core.config import Settings
from x_agent.infrastructure.composite_sql_knowledge_base import CompositeSqlKnowledgeBase
from x_agent.infrastructure.in_memory_sql_knowledge_base import InMemorySqlKnowledgeBase
from x_agent.infrastructure.mysql_metadata_sql_knowledge_base import MysqlMetadataSqlKnowledgeBase
from x_agent.infrastructure.qdrant_sql_knowledge_base import QdrantSqlKnowledgeBase
from x_agent.main import create_agent_executor, create_nl2sql_knowledge_base


def make_settings(
    *,
    llm_provider: str = "simple",
    qwen_api_key: str | None = None,
    nl2sql_knowledge_source: str = "mysql",
) -> Settings:
    return Settings(
        _env_file=None,
        llm_provider=llm_provider,
        qwen_api_key=qwen_api_key,
        nl2sql_knowledge_source=nl2sql_knowledge_source,
    )


def test_create_agent_executor_defaults_to_simple_agent() -> None:
    executor = create_agent_executor(make_settings())

    assert isinstance(executor._agent, SimpleAgent)


def test_create_agent_executor_uses_qwen_agent_when_configured() -> None:
    executor = create_agent_executor(
        make_settings(
            llm_provider="qwen",
            qwen_api_key="test-key",
        ),
    )

    assert isinstance(executor._agent, QwenAgent)


def test_create_agent_executor_requires_qwen_api_key() -> None:
    with pytest.raises(RuntimeError, match="Qwen provider requires"):
        create_agent_executor(make_settings(llm_provider="qwen"))


def test_settings_rejects_unknown_nl2sql_knowledge_source() -> None:
    with pytest.raises(ValueError, match="nl2sql_knowledge_source"):
        make_settings(nl2sql_knowledge_source="unknown")


def test_create_nl2sql_knowledge_base_defaults_to_mysql_and_static_knowledge() -> None:
    knowledge_base = create_nl2sql_knowledge_base(make_settings())

    assert isinstance(knowledge_base, CompositeSqlKnowledgeBase)
    assert any(
        isinstance(inner, MysqlMetadataSqlKnowledgeBase) for inner in knowledge_base.knowledge_bases
    )
    assert any(
        isinstance(inner, InMemorySqlKnowledgeBase) for inner in knowledge_base.knowledge_bases
    )


def test_create_nl2sql_knowledge_base_can_use_in_memory_source() -> None:
    knowledge_base = create_nl2sql_knowledge_base(make_settings(nl2sql_knowledge_source="memory"))

    assert isinstance(knowledge_base, InMemorySqlKnowledgeBase)


def test_create_nl2sql_knowledge_base_uses_mysql_and_static_knowledge() -> None:
    knowledge_base = create_nl2sql_knowledge_base(
        make_settings(nl2sql_knowledge_source="mysql"),
    )

    assert isinstance(knowledge_base, CompositeSqlKnowledgeBase)
    assert any(
        isinstance(inner, MysqlMetadataSqlKnowledgeBase) for inner in knowledge_base.knowledge_bases
    )
    assert any(
        isinstance(inner, InMemorySqlKnowledgeBase) for inner in knowledge_base.knowledge_bases
    )


def test_create_nl2sql_knowledge_base_can_use_vector_source() -> None:
    knowledge_base = create_nl2sql_knowledge_base(
        make_settings(
            nl2sql_knowledge_source="vector",
            qwen_api_key="test-key",
        ),
    )

    assert isinstance(knowledge_base, QdrantSqlKnowledgeBase)
