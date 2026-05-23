from collections.abc import Iterator
from dataclasses import dataclass, field

from x_agent.domain.agent_message import AgentMessage


@dataclass(frozen=True, slots=True)
class AgentReply:
    content: str
    metadata: dict[str, str]


@dataclass(frozen=True, slots=True)
class AgentReplyChunk:
    content_delta: str
    metadata: dict[str, str] = field(default_factory=dict)


class SimpleAgent:
    def reply_to(self, message: AgentMessage) -> AgentReply:
        return AgentReply(
            content=(
                f'已收到你的任务: "{message.content}". '
                "当前 Agent 执行层还未接入 LLM, 下一步将支持 Provider 调用。"
            ),
            metadata={
                "agent": "simple",
                "mode": "deterministic",
            },
        )

    def stream_reply_to(self, message: AgentMessage) -> Iterator[AgentReplyChunk]:
        reply = self.reply_to(message)
        yield AgentReplyChunk(content_delta=reply.content, metadata=reply.metadata)
