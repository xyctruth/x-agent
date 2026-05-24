from x_agent.application.embeddings import EmbeddingProvider
from x_agent.application.nl2sql_knowledge_ingest import Nl2SqlKnowledgeIngestService
from x_agent.domain.nl2sql import SqlKnowledgeItem


class FakeEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        self.texts: tuple[str, ...] = ()

    def embed_texts(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        self.texts = texts
        return tuple((float(index), float(len(text))) for index, text in enumerate(texts))


class FakeVectorStore:
    def __init__(self) -> None:
        self.vector_size: int | None = None
        self.upserted_items: tuple[SqlKnowledgeItem, ...] = ()
        self.upserted_vectors: tuple[tuple[float, ...], ...] = ()

    def ensure_collection(self, *, vector_size: int) -> None:
        self.vector_size = vector_size

    def upsert_items(
        self,
        *,
        items: tuple[SqlKnowledgeItem, ...],
        vectors: tuple[tuple[float, ...], ...],
    ) -> None:
        self.upserted_items = items
        self.upserted_vectors = vectors


def test_ingest_service_embeds_items_and_upserts_vectors() -> None:
    embedding_provider = FakeEmbeddingProvider()
    vector_store = FakeVectorStore()
    service = Nl2SqlKnowledgeIngestService(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        vector_size=2,
    )
    items = (
        SqlKnowledgeItem(
            id="metric:order_count",
            type="metric",
            name="订单数",
            content="订单数使用 COUNT(DISTINCT fact_orders.id) 计算。",
        ),
        SqlKnowledgeItem(
            id="table:fact_orders",
            type="table",
            name="订单事实表",
            content="fact_orders(id, created_at)",
            metadata={"table_name": "fact_orders"},
        ),
    )

    result = service.ingest(items)

    assert result.item_count == 2
    assert vector_store.vector_size == 2
    assert vector_store.upserted_items == items
    assert embedding_provider.texts == (
        "type:metric\nname:订单数\ncontent:订单数使用 COUNT(DISTINCT fact_orders.id) 计算。",
        (
            "type:table\nname:订单事实表\ncontent:fact_orders(id, created_at)\n"
            "table_name:fact_orders"
        ),
    )
    assert vector_store.upserted_vectors == ((0.0, 69.0), (1.0, 80.0))
