from x_agent.application.service_info import ServiceInfoService
from x_agent.core.config import Settings


def test_get_service_info_returns_service_metadata() -> None:
    settings = Settings(service_name="test-agent", service_version="9.9.9")
    service = ServiceInfoService(settings=settings)

    info = service.get_service_info()

    assert info.name == "test-agent"
    assert info.version == "9.9.9"
    assert "service health" in info.responsibilities
    assert "agent" in info.layers
