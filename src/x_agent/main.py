from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from x_agent.agent.qwen_agent import QwenAgent
from x_agent.agent.simple_agent import SimpleAgent
from x_agent.api.v1.router import router as api_v1_router
from x_agent.core.config import Settings, get_settings
from x_agent.core.logging import configure_logging
from x_agent.execution.agent_executor import AgentExecutor
from x_agent.infrastructure.qwen_llm_provider import QwenLLMProvider
from x_agent.persistence.in_memory_agent_message_repository import (
    InMemoryAgentMessageRepository,
)
from x_agent.persistence.in_memory_agent_session_repository import (
    InMemoryAgentSessionRepository,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.service_name,
        version=settings.service_version,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.agent_session_repository = InMemoryAgentSessionRepository()
    app.state.agent_message_repository = InMemoryAgentMessageRepository()
    app.state.agent_executor = create_agent_executor(settings)
    app.include_router(api_v1_router)
    return app


def create_agent_executor(settings: Settings) -> AgentExecutor:
    if settings.llm_provider == "qwen":
        if settings.qwen_api_key is None:
            raise RuntimeError(
                "Qwen provider requires X_AGENT_QWEN_API_KEY or DASHSCOPE_API_KEY",
            )
        return AgentExecutor(
            agent=QwenAgent(
                provider=QwenLLMProvider(
                    api_key=settings.qwen_api_key,
                    base_url=settings.qwen_base_url,
                    model=settings.qwen_model,
                    timeout_seconds=settings.qwen_timeout_seconds,
                ),
            ),
        )

    return AgentExecutor(agent=SimpleAgent())


app = create_app()
