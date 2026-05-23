import pytest

from x_agent.agent.qwen_agent import QwenAgent
from x_agent.agent.simple_agent import SimpleAgent
from x_agent.core.config import Settings
from x_agent.main import create_agent_executor


def test_create_agent_executor_defaults_to_simple_agent() -> None:
    executor = create_agent_executor(Settings())

    assert isinstance(executor._agent, SimpleAgent)


def test_create_agent_executor_uses_qwen_agent_when_configured() -> None:
    executor = create_agent_executor(
        Settings(
            llm_provider="qwen",
            qwen_api_key="test-key",
        ),
    )

    assert isinstance(executor._agent, QwenAgent)


def test_create_agent_executor_requires_qwen_api_key() -> None:
    with pytest.raises(RuntimeError, match="Qwen provider requires"):
        create_agent_executor(Settings(llm_provider="qwen"))
