from x_agent.application.agent_sessions import AgentSessionRepository
from x_agent.domain.agent_session import AgentSession


class InMemoryAgentSessionRepository(AgentSessionRepository):
    def __init__(self) -> None:
        self._sessions: dict[str, AgentSession] = {}

    def save(self, session: AgentSession) -> AgentSession:
        self._sessions[session.id] = session
        return session

    def get_by_id(self, session_id: str) -> AgentSession | None:
        return self._sessions.get(session_id)
