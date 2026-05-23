from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Literal, Protocol

LLMMessageRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True, slots=True)
class LLMMessage:
    role: LLMMessageRole
    content: str


@dataclass(frozen=True, slots=True)
class LLMCompletion:
    content: str
    provider: str
    model: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LLMCompletionChunk:
    content_delta: str
    provider: str
    model: str
    metadata: dict[str, str] = field(default_factory=dict)


class LLMProvider(Protocol):
    def complete(self, messages: tuple[LLMMessage, ...]) -> LLMCompletion: ...

    def stream_complete(
        self,
        messages: tuple[LLMMessage, ...],
    ) -> Iterator[LLMCompletionChunk]: ...


class LLMProviderError(Exception):
    pass
