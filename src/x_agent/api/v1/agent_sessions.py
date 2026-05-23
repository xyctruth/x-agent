import json
from collections.abc import Iterator
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from x_agent.api.v1.schemas import (
    AgentMessageCreateRequest,
    AgentMessageResponse,
    AgentMessageSendResponse,
    AgentSessionCreateRequest,
    AgentSessionResponse,
)
from x_agent.application.agent_messages import (
    AgentExecutor,
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
from x_agent.application.llm import LLMProviderError

router = APIRouter(prefix="/api/v1/agent-sessions", tags=["agent-sessions"])


def get_agent_session_repository(request: Request) -> AgentSessionRepository:
    return cast(AgentSessionRepository, request.app.state.agent_session_repository)


def get_agent_message_repository(request: Request) -> AgentMessageRepository:
    return cast(AgentMessageRepository, request.app.state.agent_message_repository)


def get_agent_executor(request: Request) -> AgentExecutor:
    return cast(AgentExecutor, request.app.state.agent_executor)


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
    agent_executor: Annotated[AgentExecutor, Depends(get_agent_executor)],
) -> AgentMessageService:
    return AgentMessageService(
        session_repository=session_repository,
        message_repository=message_repository,
        agent_executor=agent_executor,
    )


def encode_sse_event(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


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
) -> AgentMessageSendResponse:
    try:
        messages = service.send_user_message(
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
    except LLMProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Agent execution failed",
        ) from exc
    return AgentMessageSendResponse(
        messages=tuple(AgentMessageResponse.model_validate(message) for message in messages),
    )


@router.post("/{session_id}/messages/stream")
async def stream_agent_message(
    session_id: str,
    request: AgentMessageCreateRequest,
    service: Annotated[AgentMessageService, Depends(get_agent_message_service)],
) -> StreamingResponse:
    try:
        service.list_messages(session_id)
    except AgentSessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found",
        ) from exc

    def event_stream() -> Iterator[str]:
        try:
            for stream_event in service.stream_user_message(
                CreateAgentMessageCommand(
                    session_id=session_id,
                    content=request.content,
                    metadata=request.metadata,
                ),
            ):
                if stream_event.type == "assistant_delta":
                    yield encode_sse_event(
                        "assistant_delta",
                        json.dumps(
                            {"content": stream_event.content_delta},
                            ensure_ascii=False,
                        ),
                    )
                    continue

                if stream_event.message is None:
                    continue

                yield encode_sse_event(
                    stream_event.type,
                    AgentMessageResponse.model_validate(
                        stream_event.message,
                    ).model_dump_json(),
                )
            yield encode_sse_event("done", "{}")
        except LLMProviderError:
            yield encode_sse_event(
                "error",
                json.dumps({"detail": "Agent execution failed"}),
            )

    return StreamingResponse(event_stream(), media_type="text/event-stream")


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
