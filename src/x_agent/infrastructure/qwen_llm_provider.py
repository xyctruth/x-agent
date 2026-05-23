import json
from collections.abc import Iterator, Mapping
from typing import Any

import httpx

from x_agent.application.llm import (
    LLMCompletion,
    LLMCompletionChunk,
    LLMMessage,
    LLMProviderError,
)

HTTP_ERROR_STATUS = 400


class QwenLLMProvider:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
        client: httpx.Client | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("Qwen API key is required")

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._owns_client = client is None

    def complete(self, messages: tuple[LLMMessage, ...]) -> LLMCompletion:
        try:
            response = self._client.post(
                f"{self._base_url}/chat/completions",
                headers=self._headers(),
                json=self._request_payload(messages),
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LLMProviderError(self._format_error_response(exc.response)) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Qwen request failed: {exc}") from exc

        payload = response.json()
        return LLMCompletion(
            content=self._extract_content(payload),
            provider="qwen",
            model=str(payload.get("model") or self._model),
            metadata=self._extract_usage_metadata(payload),
        )

    def stream_complete(
        self,
        messages: tuple[LLMMessage, ...],
    ) -> Iterator[LLMCompletionChunk]:
        try:
            with self._client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                headers=self._headers(),
                json={
                    **self._request_payload(messages),
                    "stream": True,
                    "stream_options": {"include_usage": True},
                },
            ) as response:
                if response.status_code >= HTTP_ERROR_STATUS:
                    response.read()
                    response.raise_for_status()

                for line in response.iter_lines():
                    payload = self._parse_stream_line(line)
                    if payload is None:
                        continue

                    content_delta = self._extract_delta_content(payload)
                    metadata = self._extract_usage_metadata(payload)
                    if not content_delta and not metadata:
                        continue

                    yield LLMCompletionChunk(
                        content_delta=content_delta,
                        provider="qwen",
                        model=str(payload.get("model") or self._model),
                        metadata=metadata,
                    )
        except httpx.HTTPStatusError as exc:
            raise LLMProviderError(self._format_error_response(exc.response)) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Qwen stream request failed: {exc}") from exc

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _request_payload(self, messages: tuple[LLMMessage, ...]) -> dict[str, object]:
        return {
            "model": self._model,
            "messages": [
                {
                    "role": message.role,
                    "content": message.content,
                }
                for message in messages
            ],
        }

    def _extract_content(self, payload: Mapping[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LLMProviderError("Qwen response missing choices")

        first_choice = choices[0]
        if not isinstance(first_choice, Mapping):
            raise LLMProviderError("Qwen response choice is invalid")

        message = first_choice.get("message")
        if not isinstance(message, Mapping):
            raise LLMProviderError("Qwen response missing message")

        content = message.get("content")
        if not isinstance(content, str) or not content:
            raise LLMProviderError("Qwen response message content is empty")

        return content

    def _extract_delta_content(self, payload: Mapping[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""

        first_choice = choices[0]
        if not isinstance(first_choice, Mapping):
            return ""

        delta = first_choice.get("delta")
        if not isinstance(delta, Mapping):
            return ""

        content = delta.get("content")
        return content if isinstance(content, str) else ""

    def _extract_usage_metadata(self, payload: Mapping[str, Any]) -> dict[str, str]:
        usage = payload.get("usage")
        if not isinstance(usage, Mapping):
            return {}

        metadata: dict[str, str] = {}
        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            value = usage.get(key)
            if isinstance(value, int):
                metadata[key] = str(value)
        return metadata

    def _parse_stream_line(self, line: str) -> Mapping[str, Any] | None:
        if not line:
            return None
        if not line.startswith("data:"):
            return None

        data = line.removeprefix("data:").strip()
        if not data or data == "[DONE]":
            return None

        try:
            payload = json.loads(data)
        except json.JSONDecodeError as exc:
            raise LLMProviderError("Qwen stream response line is invalid JSON") from exc

        if not isinstance(payload, Mapping):
            raise LLMProviderError("Qwen stream response line is invalid")
        return payload

    def _format_error_response(self, response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return f"Qwen request failed with status {response.status_code}"

        error = payload.get("error")
        if isinstance(error, Mapping):
            message = error.get("message")
            code = error.get("code")
            if isinstance(message, str):
                if isinstance(code, str):
                    return f"Qwen request failed: {code}: {message}"
                return f"Qwen request failed: {message}"

        return f"Qwen request failed with status {response.status_code}"
