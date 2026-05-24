from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]: ...


class EmbeddingProviderError(Exception):
    pass
