from collections.abc import Iterator
from typing import Protocol

from x_agent.agent.simple_agent import AgentReply, AgentReplyChunk
from x_agent.domain.agent_message import AgentMessage


class Agent(Protocol):
    def reply_to(self, message: AgentMessage) -> AgentReply: ...

    def stream_reply_to(self, message: AgentMessage) -> Iterator[AgentReplyChunk]: ...


class AgentExecutor:
    def __init__(self, *, agent: Agent) -> None:
        self._agent = agent

    def execute(self, message: AgentMessage) -> AgentReply:
        return self._agent.reply_to(message)

    def stream_execute(self, message: AgentMessage) -> Iterator[AgentReplyChunk]:
        yield from self._agent.stream_reply_to(message)
