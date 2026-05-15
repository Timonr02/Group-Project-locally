import logging
import asyncpg
from fastapi import HTTPException, status
from config import settings

logger = logging.getLogger(__name__)


class DatabasePoolManager:
    """Manager for asyncpg connection pool."""

    _pool = None

    @classmethod
    async def initialize(cls) -> None:
        """Initialize the database connection pool."""
        try:
            cls._pool = await asyncpg.create_pool(
                dsn=settings.db_dsn,
                min_size=2,
                max_size=20,
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    @classmethod
    async def close(cls) -> None:
        """Close the database connection pool."""
        if cls._pool:
            await cls._pool.close()
            logger.info("Database connection pool closed")

    @classmethod
    def get_pool(cls) -> asyncpg.Pool:
        """Retrieve the active connection pool."""
        if not cls._pool:
            logger.error("Database pool access attempted before initialization")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database pool not initialized.",
            )
        return cls._pool