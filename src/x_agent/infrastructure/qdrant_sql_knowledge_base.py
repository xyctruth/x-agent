from dataclasses import dataclass
from importlib import import_module
from typing import Any, Protocol, cast
from uuid import NAMESPACE_URL, uuid5

from x_agent.application.embeddings import EmbeddingProvider
from x_agent.domain.nl2sql import SqlKnowledgeItem, SqlKnowledgeType, SqlRetrievalPlanStep


@dataclass(frozen=True, slots=True)
class VectorKnowledgeRecord:
    item: SqlKnowledgeItem
    score: float


class VectorSearchStore(Protocol):
    def search(
        self,
        *,
        query_vector: tuple[float, ...],
        limit: int,
        knowledge_types: tuple[SqlKnowledgeType, ...],
        score_threshold: float | None,
    ) -> tuple[VectorKnowledgeRecord, ...]: ...


class QdrantVectorStore:
    def __init__(
        self,
        *,
        url: str,
        collection_name: str,
        timeout_seconds: float,
        client: Any | None = None,
    ) -> None:
        self._collection_name = collection_name
        self._client = client or self._create_client(url=url, timeout_seconds=timeout_seconds)

    def ensure_collection(self, *, vector_size: int) -> None:
        models = import_module("qdrant_client.models")
        if self._client.collection_exists(collection_name=self._collection_name):
            return
        self._client.create_collection(
            collection_name=self._collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    def upsert_items(
        self,
        *,
        items: tuple[SqlKnowledgeItem, ...],
        vectors: tuple[tuple[float, ...], ...],
    ) -> None:
        if len(items) != len(vectors):
            raise ValueError("items and vectors length must match")

        models = import_module("qdrant_client.models")
        points = [
            models.PointStruct(
                id=str(uuid5(NAMESPACE_URL, item.id)),
                vector=list(vector),
                payload=self._item_to_payload(item),
            )
            for item, vector in zip(items, vectors, strict=True)
        ]
        if not points:
            return
        self._client.upsert(
            collection_name=self._collection_name,
            points=points,
            wait=True,
        )

    def search(
        self,
        *,
        query_vector: tuple[float, ...],
        limit: int,
        knowledge_types: tuple[SqlKnowledgeType, ...],
        score_threshold: float | None,
    ) -> tuple[VectorKnowledgeRecord, ...]:
        models = import_module("qdrant_client.models")
        response = self._client.query_points(
            collection_name=self._collection_name,
            query=list(query_vector),
            limit=limit,
            with_payload=True,
            query_filter=self._build_type_filter(models, knowledge_types),
            score_threshold=score_threshold,
        )
        points = getattr(response, "points", response)
        return tuple(self._point_to_record(point) for point in points)

    def _create_client(self, *, url: str, timeout_seconds: float) -> Any:
        qdrant_client = import_module("qdrant_client")
        return qdrant_client.QdrantClient(
            url=url,
            timeout=timeout_seconds,
            trust_env=False,
            check_compatibility=False,
        )

    def _item_to_payload(self, item: SqlKnowledgeItem) -> dict[str, object]:
        return {
            "id": item.id,
            "type": item.type,
            "name": item.name,
            "content": item.content,
            "metadata": item.metadata,
        }

    def _point_to_record(self, point: Any) -> VectorKnowledgeRecord:
        payload = cast("dict[str, object]", getattr(point, "payload", {}) or {})
        return VectorKnowledgeRecord(
            item=SqlKnowledgeItem(
                id=str(payload["id"]),
                type=cast("SqlKnowledgeType", str(payload["type"])),
                name=str(payload["name"]),
                content=str(payload["content"]),
                metadata=cast("dict[str, str]", payload.get("metadata") or {}),
            ),
            score=float(getattr(point, "score", 0.0)),
        )

    def _build_type_filter(
        self,
        models: Any,
        knowledge_types: tuple[SqlKnowledgeType, ...],
    ) -> Any | None:
        if not knowledge_types:
            return None
        return models.Filter(
            must=[
                models.FieldCondition(
                    key="type",
                    match=models.MatchAny(any=list(knowledge_types)),
                ),
            ],
        )


class QdrantSqlKnowledgeBase:
    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorSearchStore,
        top_k: int,
        score_threshold: float | None,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._top_k = top_k
        self._score_threshold = score_threshold

    def search(self, step: SqlRetrievalPlanStep) -> tuple[SqlKnowledgeItem, ...]:
        query_text = f"{step.query}\n{step.reason}"
        query_vector = self._embedding_provider.embed_texts((query_text,))[0]
        records = self._vector_store.search(
            query_vector=query_vector,
            limit=self._top_k,
            knowledge_types=step.knowledge_types,
            score_threshold=self._score_threshold,
        )
        items_by_id: dict[str, SqlKnowledgeItem] = {}
        for record in records:
            items_by_id.setdefault(record.item.id, record.item)
            if len(items_by_id) >= self._top_k:
                break
        return tuple(items_by_id.values())
