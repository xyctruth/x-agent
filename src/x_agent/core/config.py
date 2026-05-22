from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="X_AGENT_",
        extra="ignore",
    )

    service_name: str = "x-agent"
    service_version: str = "0.1.0"
    environment: str = "local"
    log_level: str = "INFO"
    cors_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(origin.strip() for origin in value.split(",") if origin.strip())
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
