from collections.abc import Iterator

from x_agent.agent.simple_agent import AgentReply, AgentReplyChunk
from x_agent.application.llm import LLMMessage, LLMProvider
from x_agent.domain.agent_message import AgentMessage


class QwenAgent:
    def __init__(self, *, provider: LLMProvider) -> None:
        self._provider = provider

    def reply_to(self, message: AgentMessage) -> AgentReply:
        completion = self._provider.complete(self._build_messages(message))
        return AgentReply(
            content=completion.content,
            metadata={
                "agent": "qwen",
                "provider": completion.provider,
                "model": completion.model,
                **completion.metadata,
            },
        )

    def stream_reply_to(self, message: AgentMessage) -> Iterator[AgentReplyChunk]:
        for chunk in self._provider.stream_complete(self._build_messages(message)):
            yield AgentReplyChunk(
                content_delta=chunk.content_delta,
                metadata={
                    "agent": "qwen",
                    "provider": chunk.provider,
                    "model": chunk.model,
                    **chunk.metadata,
                },
            )

    def _build_messages(self, message: AgentMessage) -> tuple[LLMMessage, ...]:
        return (
            LLMMessage(
                role="system",
                content="你是 x-agent 服务中的 AI Agent, 请用简洁、可靠的中文回答用户。",
            ),
            LLMMessage(role="user", content=message.content),
        )
