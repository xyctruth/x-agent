from x_agent.agent.simple_agent import SimpleAgent
from x_agent.domain.agent_message import AgentMessage
from x_agent.execution.agent_executor import AgentExecutor


def test_agent_executor_delegates_to_agent() -> None:
    executor = AgentExecutor(agent=SimpleAgent())
    message = AgentMessage.create_user_message(
        message_id="message-1",
        session_id="session-1",
        content="你好",
    )

    reply = executor.execute(message)

    assert "你好" in reply.content
    assert reply.metadata["agent"] == "simple"
