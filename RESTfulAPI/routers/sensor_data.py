import logging
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from asyncpg import Connection

from database import DatabasePoolManager
from models import (
    MetricsResponse, 
    SensorMetric, 
    CMMSDataInsert, 
    CMMSMetricsResponse, 
    CMMSDataResponse,
    EventsResponse,
    MachineEvent
)

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


@router.get("/{machine}/events", response_model=EventsResponse)
async def get_machine_events(
    machine: str,
    event_names: Optional[str] = Query(None, description="Comma-separated event names. Leave empty for all."),
    limit: int = Query(1000, le=10000),
    db: Connection = Depends(get_db_connection),
):
    """Retrieve text/log events from the machine_events table. Example: GET /api/v1/delta_robot/events"""
    
    query = "SELECT time, event_name, message FROM machine_events WHERE machine_id = $1"
    params = [machine]
    
    if event_names:
        event_list = [e.strip() for e in event_names.split(",")]
        placeholders = ",".join([f"${i+2}" for i in range(len(event_list))])
        query += f" AND event_name IN ({placeholders})"
        params.extend(event_list)
        
    query += f" ORDER BY time DESC LIMIT ${len(params) + 1}"
    params.append(limit)
    
    rows = await db.fetch(query, *params)
    events = [
        MachineEvent(timestamp=r["time"], event_name=r["event_name"], message=r["message"]) 
        for r in rows
    ]
    return EventsResponse(
        events=events,
        count=len(events),
        query_params={"machine": machine, "event_names": event_names}
    )


@router.post("/cmms", status_code=status.HTTP_201_CREATED, summary="Store CMMS/AAS data")
async def insert_cmms_data(
    payload: CMMSDataInsert,
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


@router.get("/cmms/{machine_id}", response_model=CMMSMetricsResponse)
async def get_cmms_metrics(
    machine_id: str,
    metrics: Optional[str] = Query(None, description="Comma-separated metric names. Leave empty for all."),
    limit: int = Query(1000, le=10000),
    db: Connection = Depends(get_db_connection),
):
    """Retrieve stored CMMS/AAS metrics for a specific machine. Example: GET /api/v1/cmms/laser_01"""
    
    query = "SELECT time, machine_id, metric_name, value FROM cmms_data WHERE machine_id = $1"
    params = [machine_id]
    
    if metrics:
        metric_list = [m.strip() for m in metrics.split(",")]
        placeholders = ",".join([f"${i+2}" for i in range(len(metric_list))])
        query += f" AND metric_name IN ({placeholders})"
        params.extend(metric_list)
        
    query += f" ORDER BY time DESC LIMIT ${len(params) + 1}"
    params.append(limit)
    
    rows = await db.fetch(query, *params)
    metrics_list = [
        CMMSDataResponse(
            time=r["time"],
            machine_id=r["machine_id"],
            metric_name=r["metric_name"],
            value=r["value"]
        ) for r in rows
    ]
    return CMMSMetricsResponse(metrics=metrics_list, count=len(metrics_list))