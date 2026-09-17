"""Application configuration for NetOps Sentinel."""

from enum import StrEnum
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Supported application environments."""

    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class ModelProvider(StrEnum):
    """Supported AI model providers."""

    MOCK = "mock"
    NEBIUS = "nebius"


class LogLevel(StrEnum):
    """Supported application log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """Validated configuration for NetOps Sentinel."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    netops_environment: Environment = Environment.DEVELOPMENT
    netops_log_level: LogLevel = LogLevel.INFO
    netops_model_provider: ModelProvider = ModelProvider.MOCK

    nebius_api_key: SecretStr | None = None
    nebius_base_url: str | None = None
    nebius_model: str | None = None

    langsmith_tracing: bool = False
    langsmith_api_key: SecretStr | None = None
    langsmith_project: str = "netops-sentinel"

    database_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""

    return Settings()
