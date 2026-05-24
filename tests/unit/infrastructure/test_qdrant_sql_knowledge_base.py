from typing import Any

import pytest

import x_agent.infrastructure.qdrant_sql_knowledge_base as qdrant_module
from x_agent.application.embeddings import EmbeddingProvider
from x_agent.domain.nl2sql import SqlKnowledgeItem, SqlKnowledgeType, SqlRetrievalPlanStep
from x_agent.infrastructure.qdrant_sql_knowledge_base import (
    QdrantSqlKnowledgeBase,
    QdrantVectorStore,
    VectorKnowledgeRecord,
)


class FakeEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        self.texts: tuple[str, ...] = ()

    def embed_texts(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        self.texts = texts
        return ((0.1, 0.2),)


class FakeVectorStore:
    def __init__(self, records: tuple[VectorKnowledgeRecord, ...]) -> None:
        self.records = records
        self.query_vector: tuple[float, ...] = ()
        self.limit: int | None = None
        self.knowledge_types: tuple[SqlKnowledgeType, ...] = ()
        self.score_threshold: float | None = None

    def search(
        self,
        *,
        query_vector: tuple[float, ...],
        limit: int,
        knowledge_types: tuple[SqlKnowledgeType, ...],
        score_threshold: float | None,
    ) -> tuple[VectorKnowledgeRecord, ...]:
        self.query_vector = query_vector
        self.limit = limit
        self.knowledge_types = knowledge_types
        self.score_threshold = score_threshold
        return self.records


class FakeQdrantPoint:
    def __init__(self, *, payload: dict[str, object], score: float) -> None:
        self.payload = payload
        self.score = score


class FakeQdrantQueryResponse:
    def __init__(self, points: tuple[FakeQdrantPoint, ...]) -> None:
        self.points = points


class FakeQdrantClient:
    def __init__(self) -> None:
        self.created_collection: str | None = None
        self.vector_size: int | None = None
        self.upserted_points: list[Any] = []
        self.query_filter: Any | None = None
        self.score_threshold: float | None = None

    def collection_exists(self, *, collection_name: str) -> bool:
        return False

    def create_collection(self, *, collection_name: str, vectors_config: Any) -> None:
        self.created_collection = collection_name
        self.vector_size = vectors_config.size

    def upsert(self, *, collection_name: str, points: list[Any], wait: bool) -> None:
        self.upserted_points = points

    def query_points(self, **kwargs: Any) -> FakeQdrantQueryResponse:
        self.query_filter = kwargs.get("query_filter")
        self.score_threshold = kwargs.get("score_threshold")
        return FakeQdrantQueryResponse(
            points=(
                FakeQdrantPoint(
                    payload={
                        "id": "table:fact_orders",
                        "type": "table",
                        "name": "订单事实表",
                        "content": "fact_orders(id)",
                        "metadata": {"table_name": "fact_orders"},
                    },
                    score=0.93,
                ),
            ),
        )


def test_qdrant_sql_knowledge_base_returns_top_matching_types() -> None:
    embedding_provider = FakeEmbeddingProvider()
    vector_store = FakeVectorStore(
        records=(
            VectorKnowledgeRecord(
                item=SqlKnowledgeItem(
                    id="table:fact_orders",
                    type="table",
                    name="订单事实表",
                    content="fact_orders(id, created_at)",
                    metadata={"table_name": "fact_orders"},
                ),
                score=0.88,
            ),
            VectorKnowledgeRecord(
                item=SqlKnowledgeItem(
                    id="metric:order_count",
                    type="metric",
                    name="订单数",
                    content="订单数使用 COUNT(DISTINCT fact_orders.id) 计算。",
                ),
                score=0.91,
            ),
        ),
    )
    knowledge_base = QdrantSqlKnowledgeBase(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        top_k=1,
        score_threshold=0.5,
    )

    items = knowledge_base.search(
        SqlRetrievalPlanStep(
            query="统计订单数",
            knowledge_types=("table",),
            reason="检索表结构",
        ),
    )

    assert embedding_provider.texts == ("统计订单数\n检索表结构",)
    assert vector_store.query_vector == (0.1, 0.2)
    assert vector_store.limit == 1
    assert vector_store.knowledge_types == ("table",)
    assert vector_store.score_threshold == 0.5
    assert [item.id for item in items] == ["table:fact_orders"]


def test_qdrant_vector_store_maps_items_to_points_and_records() -> None:
    client = FakeQdrantClient()
    vector_store = QdrantVectorStore(
        url="http://127.0.0.1:6333",
        collection_name="nl2sql_knowledge",
        timeout_seconds=10,
        client=client,
    )
    item = SqlKnowledgeItem(
        id="table:fact_orders",
        type="table",
        name="订单事实表",
        content="fact_orders(id)",
        metadata={"table_name": "fact_orders"},
    )

    vector_store.ensure_collection(vector_size=2)
    vector_store.upsert_items(items=(item,), vectors=((0.1, 0.2),))
    records = vector_store.search(
        query_vector=(0.1, 0.2),
        limit=1,
        knowledge_types=("table", "metric"),
        score_threshold=0.5,
    )

    assert client.created_collection == "nl2sql_knowledge"
    assert client.vector_size == 2
    assert len(client.upserted_points) == 1
    assert client.upserted_points[0].vector == [0.1, 0.2]
    assert client.upserted_points[0].payload["id"] == "table:fact_orders"
    assert client.query_filter is not None
    assert client.query_filter.must[0].key == "type"
    assert client.query_filter.must[0].match.any == ["table", "metric"]
    assert client.score_threshold == 0.5
    assert records == (
        VectorKnowledgeRecord(
            item=item,
            score=0.93,
        ),
    )


def test_qdrant_vector_store_disables_environment_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_kwargs: dict[str, object] = {}

    class FakeQdrantClientModule:
        class QdrantClient:
            def __init__(self, **kwargs: object) -> None:
                captured_kwargs.update(kwargs)

    def fake_import_module(name: str) -> object:
        if name == "qdrant_client":
            return FakeQdrantClientModule
        return __import__(name)

    monkeypatch.setattr(qdrant_module, "import_module", fake_import_module)

    QdrantVectorStore(
        url="http://127.0.0.1:6333",
        collection_name="nl2sql_knowledge",
        timeout_seconds=10,
    )

    assert captured_kwargs["url"] == "http://127.0.0.1:6333"
    assert captured_kwargs["timeout"] == 10
    assert captured_kwargs["trust_env"] is False
    assert captured_kwargs["check_compatibility"] is False
