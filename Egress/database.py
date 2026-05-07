import asyncpg
from fastapi import HTTPException, status
from config import settings

class DatabasePoolManager:
    _pool: asyncpg.Pool = None

    @classmethod
    async def initialize(cls) -> None:
        cls._pool = await asyncpg.create_pool(
            dsn=settings.db_read_dsn,
            min_size=2,
            max_size=20,
            command_timeout=10.0
        )

    @classmethod
    async def close(cls) -> None:
        if cls._pool:
            await cls._pool.close()

    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        if not cls._pool:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database pool not initialized"
            )
        return cls._pool