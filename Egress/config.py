import logging
from typing import Optional

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Attributes:
        db_dsn: Database connection string for TimescaleDB access (read/write).
        cors_origins: List of allowed CORS origins (default: all origins).
    """

    db_dsn: str = Field(
        ..., description="PostgreSQL/TimescaleDB connection string for read-write access"
    )
    cors_origins: list[str] = Field(
        default=["*"], description="List of allowed CORS origins"
    )

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = False


try:
    settings = Settings()
    logger.info("Configuration loaded successfully")
except ValidationError as e:
    logger.error(f"Configuration validation failed: {e}")
    raise