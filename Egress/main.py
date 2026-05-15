import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import DatabasePoolManager
from routers import sensor_data

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    await DatabasePoolManager.initialize()
    yield
    await DatabasePoolManager.close()


app = FastAPI(
    title="Digital Factory Data API",
    description="Industrial IoT data management API. Supports reading aggregated sensor data and inserting new measurements.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sensor_data.router)