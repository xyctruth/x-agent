import json

import httpx
import pytest

from x_agent.application.llm import LLMMessage, LLMProviderError
from x_agent.infrastructure.qwen_llm_provider import QwenLLMProvider


def test_qwen_provider_sends_openai_compatible_request() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(
            200,
            json={
                "model": "qwen-plus",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "你好, 我是千问。",
                        },
                    },
                ],
                "usage": {
                    "prompt_tokens": 3,
                    "completion_tokens": 4,
                    "total_tokens": 7,
                },
            },
        )

    provider = QwenLLMProvider(
        api_key="test-key",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1/",
        model="qwen-plus",
        timeout_seconds=30,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    completion = provider.complete((LLMMessage(role="user", content="你是谁?"),))

    assert captured_request is not None
    assert str(captured_request.url) == (
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    )
    assert captured_request.headers["authorization"] == "Bearer test-key"
    assert json.loads(captured_request.content) == {
        "model": "qwen-plus",
        "messages": [
            {
                "role": "user",
                "content": "你是谁?",
            },
        ],
    }
    assert completion.content == "你好, 我是千问。"
    assert completion.provider == "qwen"
    assert completion.model == "qwen-plus"
    assert completion.metadata == {
        "prompt_tokens": "3",
        "completion_tokens": "4",
        "total_tokens": "7",
    }


def test_qwen_provider_raises_for_error_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={
                "error": {
                    "code": "invalid_api_key",
                    "message": "Incorrect API key provided.",
                },
            },
            request=request,
        )

    provider = QwenLLMProvider(
        api_key="bad-key",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-plus",
        timeout_seconds=30,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(LLMProviderError, match="invalid_api_key"):
        provider.complete((LLMMessage(role="user", content="你好"),))


def test_qwen_provider_streams_openai_compatible_chunks() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(
            200,
            text=(
                'data: {"model":"qwen-plus","choices":[{"delta":{"content":"你"}}]}\n\n'
                'data: {"model":"qwen-plus","choices":[{"delta":{"content":"好"}}]}\n\n'
                'data: {"model":"qwen-plus","choices":[],"usage":{"total_tokens":7}}\n\n'
                "data: [DONE]\n\n"
            ),
        )

    provider = QwenLLMProvider(
        api_key="test-key",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-plus",
        timeout_seconds=30,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    chunks = tuple(provider.stream_complete((LLMMessage(role="user", content="你是谁?"),)))

    assert captured_request is not None
    assert json.loads(captured_request.content) == {
        "model": "qwen-plus",
        "messages": [
            {
                "role": "user",
                "content": "你是谁?",
            },
        ],
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    assert [chunk.content_delta for chunk in chunks] == ["你", "好", ""]
    assert chunks[-1].metadata == {"total_tokens": "7"}


def test_qwen_provider_requires_api_key() -> None:
    with pytest.raises(ValueError, match="Qwen API key is required"):
        QwenLLMProvider(
            api_key="",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
            timeout_seconds=30,
        )
