from dataclasses import dataclass
from typing import Protocol

from x_agent.application.embeddings import EmbeddingProvider
from x_agent.domain.nl2sql import SqlKnowledgeItem


class VectorKnowledgeStore(Protocol):
    def ensure_collection(self, *, vector_size: int) -> None: ...

    def upsert_items(
        self,
        *,
        items: tuple[SqlKnowledgeItem, ...],
        vectors: tuple[tuple[float, ...], ...],
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class Nl2SqlKnowledgeIngestResult:
    item_count: int


class Nl2SqlKnowledgeIngestService:
    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorKnowledgeStore,
        vector_size: int,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._vector_size = vector_size

    def ingest(self, items: tuple[SqlKnowledgeItem, ...]) -> Nl2SqlKnowledgeIngestResult:
        self._vector_store.ensure_collection(vector_size=self._vector_size)
        texts = tuple(self._build_embedding_text(item) for item in items)
        vectors = self._embedding_provider.embed_texts(texts) if texts else ()
        self._vector_store.upsert_items(items=items, vectors=vectors)
        return Nl2SqlKnowledgeIngestResult(item_count=len(items))

    def _build_embedding_text(self, item: SqlKnowledgeItem) -> str:
        metadata_text = " ".join(f"{key}:{value}" for key, value in item.metadata.items())
        return "\n".join(
            part
            for part in (
                f"type:{item.type}",
                f"name:{item.name}",
                f"content:{item.content}",
                metadata_text,
            )
            if part
        )
