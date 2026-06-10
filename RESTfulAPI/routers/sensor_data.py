import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from asyncpg import Connection

from database import DatabasePoolManager
from models import MetricsResponse, SensorMetric, CMmsDataInsert

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Sensor Data"])


async def get_db_connection():
    """Acquire a database connection from the pool."""
    pool = DatabasePoolManager.get_pool()
    async with pool.acquire() as connection:
        yield connection


@router.get("/{machine}/metrics", response_model=MetricsResponse)
async def get_machine_metrics(
    machine: str,
    sensors: str = Query(..., description="Comma-separated sensor names"),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    limit: int = Query(10000, le=100000),
    db: Connection = Depends(get_db_connection),
):
    """Get metrics for any machine. Example: GET /api/v1/laser/metrics?sensors=is_running,progress"""
    
    if not machine.replace("_", "").isalnum():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid machine name")
    
    table_name = f"{machine}_data"
    sensor_list = [s.strip() for s in sensors.split(",")]
    
    placeholders = ",".join([f"${i+1}" for i in range(len(sensor_list))])
    query = f"SELECT time, sensor_name, value FROM {table_name} WHERE sensor_name IN ({placeholders})"
    
    params = list(sensor_list)
    
    if start_time:
        query += f" AND time >= ${len(params) + 1}"
        params.append(datetime.fromisoformat(start_time.replace("Z", "+00:00")))
    
    if end_time:
        query += f" AND time <= ${len(params) + 1}"
        params.append(datetime.fromisoformat(end_time.replace("Z", "+00:00")))
    
    query += f" ORDER BY time DESC LIMIT ${len(params) + 1}"
    params.append(limit)
    
    rows = await db.fetch(query, *params)
    metrics = [SensorMetric(timestamp=r["time"], sensor_name=r["sensor_name"], value=r["value"]) for r in rows]
    
    return MetricsResponse(metrics=metrics, count=len(metrics), query_params={"machine": machine, "sensors": sensor_list})


@router.post("/cmms", status_code=status.HTTP_201_CREATED, summary="Store CMMS/AAS data")
async def insert_cmms_data(
    payload: CMmsDataInsert,
    db: Connection = Depends(get_db_connection),
) -> dict:
    """Insert CMMS or AAS data."""
    timestamp = payload.timestamp or datetime.now(timezone.utc)
    
    query = """
        INSERT INTO cmms_data (time, machine_id, metric_name, value)
        VALUES ($1, $2, $3, $4)
    """
    
    try:
        await db.execute(query, timestamp, payload.machine_id, payload.metric_name, payload.value)
    except Exception as e:
        logger.error(f"Failed to insert CMMS data: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to insert data")
    
    return {"message": "Data inserted", "machine_id": payload.machine_id}