from x_agent.core.config import Settings
from x_agent.domain.service_info import ServiceInfo


class ServiceInfoService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def get_service_info(self) -> ServiceInfo:
        return ServiceInfo(
            name=self._settings.service_name,
            version=self._settings.service_version,
            responsibilities=(
                "service health",
                "service readiness",
                "service metadata",
                "agent session management",
                "agent message management",
                "agent execution",
            ),
            layers=(
                "client",
                "api",
                "application",
                "domain",
                "agent",
                "execution",
                "persistence",
                "infrastructure",
            ),
        )
