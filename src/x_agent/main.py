from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from x_agent.api.v1.router import router as api_v1_router
from x_agent.core.config import get_settings
from x_agent.core.logging import configure_logging
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
    app.state.agent_session_repository = InMemoryAgentSessionRepository()
    app.state.agent_message_repository = InMemoryAgentMessageRepository()
    app.include_router(api_v1_router)
    return app


app = create_app()
