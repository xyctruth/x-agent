from x_agent.application.agent_messages import AgentMessageRepository
from x_agent.domain.agent_message import AgentMessage


class InMemoryAgentMessageRepository(AgentMessageRepository):
    def __init__(self) -> None:
        self._messages_by_session_id: dict[str, list[AgentMessage]] = {}

    def save(self, message: AgentMessage) -> AgentMessage:
        messages = self._messages_by_session_id.setdefault(message.session_id, [])
        messages.append(message)
        return message

    def list_by_session_id(self, session_id: str) -> tuple[AgentMessage, ...]:
        return tuple(self._messages_by_session_id.get(session_id, ()))
