from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    service: str
    version: str
    status: str


class ReadinessResponse(BaseModel):
    status: str


class ServiceInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    version: str
    responsibilities: tuple[str, ...]
    layers: tuple[str, ...]
