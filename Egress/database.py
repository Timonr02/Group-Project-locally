import logging
from typing import Optional

import asyncpg
from fastapi import HTTPException, status

from config import settings

logger = logging.getLogger(__name__)


class DatabasePoolManager:
    """Singleton manager for asyncpg connection pool.

    Handles initialization, lifecycle management, and access to the
    TimescaleDB connection pool for read-write operations with error
    handling and logging.
    """

    _pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def initialize(cls) -> None:
        """Initialize the database connection pool for read-write access.

        Raises:
            Exception: If pool creation fails due to database connectivity or config issues.
        """
        try:
            cls._pool = await asyncpg.create_pool(
                dsn=settings.db_dsn,
                min_size=2,
                max_size=20,
                command_timeout=10.0,
            )
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    @classmethod
    async def close(cls) -> None:
        """Close and cleanup the database connection pool."""
        if cls._pool:
            try:
                await cls._pool.close()
                logger.info("Database connection pool closed successfully")
            except Exception as e:
                logger.error(f"Error closing database pool: {e}")
            finally:
                cls._pool = None

    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        """Retrieve the active database connection pool.

        Returns:
            The asyncpg connection pool instance.

        Raises:
            HTTPException: If the pool has not been initialized.
        """
        if not cls._pool:
            logger.error("Database pool access attempted before initialization")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database pool not initialized.",
            )
        return cls._pool