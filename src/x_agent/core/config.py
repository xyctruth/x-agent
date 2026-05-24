from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="X_AGENT_",
        extra="ignore",
        populate_by_name=True,
    )

    service_name: str = "x-agent"
    service_version: str = "0.1.0"
    environment: str = "local"
    log_level: str = "INFO"
    cors_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")
    llm_provider: str = "simple"
    qwen_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("X_AGENT_QWEN_API_KEY", "DASHSCOPE_API_KEY"),
    )
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen3.7-max"
    qwen_timeout_seconds: float = 30.0
    nl2sql_knowledge_source: str = "vector"
    embedding_provider: str = "qwen"
    qwen_embedding_model: str = "text-embedding-v4"
    embedding_dimensions: int = 1024
    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_collection: str = "nl2sql_knowledge"
    qdrant_timeout_seconds: float = 10.0
    nl2sql_vector_top_k: int = 6
    nl2sql_vector_score_threshold: float = 0.5
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = Field(default="root", repr=False)
    mysql_database: str = "x_agent_mock_biz"
    mysql_connect_timeout_seconds: float = 3.0

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(origin.strip() for origin in value.split(",") if origin.strip())
        return value

    @field_validator("llm_provider")
    @classmethod
    def normalize_llm_provider(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("nl2sql_knowledge_source")
    @classmethod
    def normalize_nl2sql_knowledge_source(cls, value: str) -> str:
        normalized_value = value.strip().lower()
        if normalized_value not in {"memory", "mysql", "vector"}:
            raise ValueError("nl2sql_knowledge_source must be memory, mysql or vector")
        return normalized_value

    @field_validator("embedding_provider")
    @classmethod
    def normalize_embedding_provider(cls, value: str) -> str:
        normalized_value = value.strip().lower()
        if normalized_value != "qwen":
            raise ValueError("embedding_provider must be qwen")
        return normalized_value


@lru_cache
def get_settings() -> Settings:
    return Settings()
