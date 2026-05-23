from fastapi import APIRouter

from x_agent.api.v1.agent_sessions import router as agent_sessions_router
from x_agent.api.v1.nl2sql import router as nl2sql_router
from x_agent.api.v1.schemas import HealthResponse, ReadinessResponse, ServiceInfoResponse
from x_agent.application.service_info import ServiceInfoService
from x_agent.core.config import get_settings

router = APIRouter()
router.include_router(agent_sessions_router)
router.include_router(nl2sql_router)


@router.get("/healthz", tags=["system"])
async def healthz() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        service=settings.service_name,
        version=settings.service_version,
        status="ok",
    )


@router.get("/readyz", tags=["system"])
async def readyz() -> ReadinessResponse:
    return ReadinessResponse(status="ready")


@router.get("/api/v1/service-info", tags=["service"])
async def service_info() -> ServiceInfoResponse:
    settings = get_settings()
    service = ServiceInfoService(settings=settings)
    info = service.get_service_info()
    return ServiceInfoResponse.model_validate(info)
