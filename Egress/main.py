from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import DatabasePoolManager
from routers import sensor_data
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    await DatabasePoolManager.initialize()
    yield
    await DatabasePoolManager.close()

app = FastAPI(
    title="Digital Factory Data API",
    description="Read-Only API for serving aggregated Industrial IoT data to CMMS and MES layers.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(sensor_data.router)