import json
from typing import cast

import httpx
import pytest

from x_agent.application.embeddings import EmbeddingProviderError
from x_agent.infrastructure.qwen_embedding_provider import (
    QwenEmbeddingConfig,
    QwenEmbeddingProvider,
)


def test_qwen_embedding_provider_sends_openai_compatible_request() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(
            200,
            json={
                "model": "text-embedding-v4",
                "data": [
                    {"index": 1, "embedding": [0.3, 0.4]},
                    {"index": 0, "embedding": [0.1, 0.2]},
                ],
                "usage": {"total_tokens": 9},
            },
        )

    provider = QwenEmbeddingProvider(
        config=QwenEmbeddingConfig(
            api_key="test-key",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1/",
            model="text-embedding-v4",
            dimensions=2,
            timeout_seconds=30,
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    embeddings = provider.embed_texts(("订单数", "支付金额"))

    assert captured_request is not None
    assert str(captured_request.url) == (
        "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
    )
    assert captured_request.headers["authorization"] == "Bearer test-key"
    assert json.loads(captured_request.content) == {
        "model": "text-embedding-v4",
        "input": ["订单数", "支付金额"],
        "dimensions": 2,
        "encoding_format": "float",
    }
    assert embeddings == ((0.1, 0.2), (0.3, 0.4))


def test_qwen_embedding_provider_batches_requests_by_dashscope_limit() -> None:
    request_payloads: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        request_payloads.append(payload)
        inputs = payload["input"]
        assert isinstance(inputs, list)
        return httpx.Response(
            200,
            json={
                "model": "text-embedding-v4",
                "data": [
                    {"index": index, "embedding": [float(index), float(len(text))]}
                    for index, text in enumerate(inputs)
                ],
            },
        )

    provider = QwenEmbeddingProvider(
        config=QwenEmbeddingConfig(
            api_key="test-key",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="text-embedding-v4",
            dimensions=2,
            timeout_seconds=30,
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    embeddings = provider.embed_texts(tuple(f"text-{index}" for index in range(12)))

    batch_sizes = [len(cast("list[str]", payload["input"])) for payload in request_payloads]
    assert batch_sizes == [10, 2]
    assert len(embeddings) == 12
    assert embeddings[0] == (0.0, 6.0)
    assert embeddings[10] == (0.0, 7.0)


def test_qwen_embedding_provider_raises_for_error_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "invalid_api_key", "message": "bad key"}},
            request=request,
        )

    provider = QwenEmbeddingProvider(
        config=QwenEmbeddingConfig(
            api_key="bad-key",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="text-embedding-v4",
            dimensions=2,
            timeout_seconds=30,
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(EmbeddingProviderError, match="invalid_api_key"):
        provider.embed_texts(("订单数",))
