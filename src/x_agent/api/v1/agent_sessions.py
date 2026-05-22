from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status

from x_agent.api.v1.schemas import (
    AgentMessageCreateRequest,
    AgentMessageResponse,
    AgentSessionCreateRequest,
    AgentSessionResponse,
)
from x_agent.application.agent_messages import (
    AgentMessageRepository,
    AgentMessageService,
    CreateAgentMessageCommand,
)
from x_agent.application.agent_sessions import (
    AgentSessionNotFoundError,
    AgentSessionRepository,
    AgentSessionService,
    CreateAgentSessionCommand,
)

router = APIRouter(prefix="/api/v1/agent-sessions", tags=["agent-sessions"])


def get_agent_session_repository(request: Request) -> AgentSessionRepository:
    return cast(AgentSessionRepository, request.app.state.agent_session_repository)


def get_agent_message_repository(request: Request) -> AgentMessageRepository:
    return cast(AgentMessageRepository, request.app.state.agent_message_repository)


def get_agent_session_service(
    repository: Annotated[AgentSessionRepository, Depends(get_agent_session_repository)],
) -> AgentSessionService:
    return AgentSessionService(repository=repository)


def get_agent_message_service(
    session_repository: Annotated[
        AgentSessionRepository,
        Depends(get_agent_session_repository),
    ],
    message_repository: Annotated[
        AgentMessageRepository,
        Depends(get_agent_message_repository),
    ],
) -> AgentMessageService:
    return AgentMessageService(
        session_repository=session_repository,
        message_repository=message_repository,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agent_session(
    request: AgentSessionCreateRequest,
    service: Annotated[AgentSessionService, Depends(get_agent_session_service)],
) -> AgentSessionResponse:
    session = service.create_session(
        CreateAgentSessionCommand(
            title=request.title,
            metadata=request.metadata,
        ),
    )
    return AgentSessionResponse.model_validate(session)


@router.post("/{session_id}/messages", status_code=status.HTTP_201_CREATED)
async def create_agent_message(
    session_id: str,
    request: AgentMessageCreateRequest,
    service: Annotated[AgentMessageService, Depends(get_agent_message_service)],
) -> AgentMessageResponse:
    try:
        message = service.create_user_message(
            CreateAgentMessageCommand(
                session_id=session_id,
                content=request.content,
                metadata=request.metadata,
            ),
        )
    except AgentSessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found",
        ) from exc
    return AgentMessageResponse.model_validate(message)


@router.get("/{session_id}/messages")
async def list_agent_messages(
    session_id: str,
    service: Annotated[AgentMessageService, Depends(get_agent_message_service)],
) -> tuple[AgentMessageResponse, ...]:
    try:
        messages = service.list_messages(session_id)
    except AgentSessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found",
        ) from exc
    return tuple(AgentMessageResponse.model_validate(message) for message in messages)


@router.get("/{session_id}")
async def get_agent_session(
    session_id: str,
    service: Annotated[AgentSessionService, Depends(get_agent_session_service)],
) -> AgentSessionResponse:
    try:
        session = service.get_session(session_id)
    except AgentSessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found",
        ) from exc
    return AgentSessionResponse.model_validate(session)
