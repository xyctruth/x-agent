from x_agent.agent.qwen_agent import QwenAgent
from x_agent.application.llm import LLMCompletion, LLMMessage
from x_agent.domain.agent_message import AgentMessage


class FakeLLMProvider:
    def __init__(self) -> None:
        self.messages: tuple[LLMMessage, ...] = ()

    def complete(self, messages: tuple[LLMMessage, ...]) -> LLMCompletion:
        self.messages = messages
        return LLMCompletion(
            content="千问回复",
            provider="qwen",
            model="qwen-plus",
            metadata={"total_tokens": "10"},
        )


def test_qwen_agent_uses_llm_provider() -> None:
    provider = FakeLLMProvider()
    agent = QwenAgent(provider=provider)
    message = AgentMessage.create_user_message(
        message_id="message-1",
        session_id="session-1",
        content="你好",
    )

    reply = agent.reply_to(message)

    assert provider.messages[0].role == "system"
    assert provider.messages[1] == LLMMessage(role="user", content="你好")
    assert reply.content == "千问回复"
    assert reply.metadata == {
        "agent": "qwen",
        "provider": "qwen",
        "model": "qwen-plus",
        "total_tokens": "10",
    }
