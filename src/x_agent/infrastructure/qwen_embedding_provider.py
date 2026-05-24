from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import httpx

from x_agent.application.embeddings import EmbeddingProviderError

HTTP_ERROR_STATUS = 400
DASHSCOPE_MAX_BATCH_SIZE = 10


@dataclass(frozen=True, slots=True)
class QwenEmbeddingConfig:
    api_key: str
    base_url: str
    model: str
    dimensions: int
    timeout_seconds: float


class QwenEmbeddingProvider:
    def __init__(
        self,
        *,
        config: QwenEmbeddingConfig,
        client: httpx.Client | None = None,
    ) -> None:
        if not config.api_key:
            raise ValueError("Qwen API key is required")

        self._config = config
        self._base_url = config.base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=config.timeout_seconds)
        self._owns_client = client is None

    def embed_texts(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        if not texts:
            return ()

        embeddings: list[tuple[float, ...]] = []
        for start_index in range(0, len(texts), DASHSCOPE_MAX_BATCH_SIZE):
            batch = texts[start_index : start_index + DASHSCOPE_MAX_BATCH_SIZE]
            embeddings.extend(self._embed_batch(batch))
        return tuple(embeddings)

    def _embed_batch(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        try:
            response = self._client.post(
                f"{self._base_url}/embeddings",
                headers=self._headers(),
                json={
                    "model": self._config.model,
                    "input": list(texts),
                    "dimensions": self._config.dimensions,
                    "encoding_format": "float",
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise EmbeddingProviderError(self._format_error_response(exc.response)) from exc
        except httpx.HTTPError as exc:
            raise EmbeddingProviderError(f"Qwen embedding request failed: {exc}") from exc

        return self._extract_embeddings(response.json(), expected_count=len(texts))

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }

    def _extract_embeddings(
        self,
        payload: Mapping[str, Any],
        *,
        expected_count: int,
    ) -> tuple[tuple[float, ...], ...]:
        data = payload.get("data")
        if not isinstance(data, list):
            raise EmbeddingProviderError("Qwen embedding response missing data")

        embeddings_by_index: dict[int, tuple[float, ...]] = {}
        for item in data:
            if not isinstance(item, Mapping):
                raise EmbeddingProviderError("Qwen embedding response item is invalid")
            index = item.get("index")
            embedding = item.get("embedding")
            if not isinstance(index, int) or not isinstance(embedding, list):
                raise EmbeddingProviderError("Qwen embedding response item is invalid")
            embeddings_by_index[index] = tuple(float(value) for value in embedding)

        try:
            return tuple(embeddings_by_index[index] for index in range(expected_count))
        except KeyError as exc:
            raise EmbeddingProviderError("Qwen embedding response missing index") from exc

    def _format_error_response(self, response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return f"Qwen embedding request failed with status {response.status_code}"

        error = payload.get("error")
        if isinstance(error, Mapping):
            message = error.get("message")
            code = error.get("code")
            if isinstance(message, str):
                if isinstance(code, str):
                    return f"Qwen embedding request failed: {code}: {message}"
                return f"Qwen embedding request failed: {message}"

        return f"Qwen embedding request failed with status {response.status_code}"
