from typing import Protocol

from x_agent.agent.simple_agent import AgentReply
from x_agent.domain.agent_message import AgentMessage


class Agent(Protocol):
    def reply_to(self, message: AgentMessage) -> AgentReply: ...


class AgentExecutor:
    def __init__(self, *, agent: Agent) -> None:
        self._agent = agent

    def execute(self, message: AgentMessage) -> AgentReply:
        return self._agent.reply_to(message)
