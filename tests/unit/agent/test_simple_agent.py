from x_agent.agent.simple_agent import SimpleAgent
from x_agent.domain.agent_message import AgentMessage


def test_simple_agent_returns_deterministic_reply() -> None:
    agent = SimpleAgent()
    message = AgentMessage.create_user_message(
        message_id="message-1",
        session_id="session-1",
        content="帮我设计 Web Client",
    )

    reply = agent.reply_to(message)

    assert "帮我设计 Web Client" in reply.content
    assert reply.metadata == {
        "agent": "simple",
        "mode": "deterministic",
    }
