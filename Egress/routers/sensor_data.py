import logging
from datetime import datetime, timezone
from typing import List

from asyncpg import Connection
from fastapi import APIRouter, Depends, HTTPException, status

from database import DatabasePoolManager
from models import SensorAggregatedResponse, SensorDataInsert

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Sensor Data"])


async def get_db_connection() -> Connection:
    """Acquire a database connection from the connection pool."""
    pool = await DatabasePoolManager.get_pool()
    async with pool.acquire() as connection:
        yield connection


@router.post(
    "/data",
    status_code=status.HTTP_201_CREATED,
    summary="Inject new sensor or AAS data",
    description="Allows external systems to inject derived metrics or manual data points "
    "directly into TimescaleDB. If no timestamp is provided, the current UTC time is used.",
)
async def insert_sensor_data(
    payload: SensorDataInsert,
    db: Connection = Depends(get_db_connection),
) -> dict:
    """
    Insert sensor data into the database.

    Args:
        payload: The sensor data to insert.
        db: Database connection from dependency injection.

    Returns:
        Dictionary with success message and machine_id.

    Raises:
        HTTPException: If database insertion fails.
    """
    timestamp = payload.timestamp or datetime.now(timezone.utc)

    query = """
        INSERT INTO sensor_data (time, machine_id, sensor_name, value)
        VALUES ($1, $2, $3, $4)
    """

    try:
        await db.execute(
            query,
            timestamp,
            payload.machine_id,
            payload.sensor_name,
            payload.value,
        )
    except Exception as e:
        logger.error(
            f"Failed to insert sensor data for machine_id={payload.machine_id}, "
            f"sensor_name={payload.sensor_name}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to insert data into the database.",
        )

    return {"message": "Data successfully injected", "machine_id": payload.machine_id}


@router.get(
    "/machines/{machine_id}/sensors/{sensor_name}",
    response_model=List[SensorAggregatedResponse],
    summary="Retrieve aggregated sensor data",
    description="Fetches historical sensor data from the TimescaleDB replica node. "
    "The data is automatically aggregated into time buckets.",
)
async def get_aggregated_sensor_data(
    machine_id: str,
    sensor_name: str,
    lookback_minutes: int = 60,
    bucket_interval_minutes: int = 5,
    db: Connection = Depends(get_db_connection),
) -> List[SensorAggregatedResponse]:
    """
    Retrieve aggregated sensor data for a specific machine and sensor.

    Args:
        machine_id: Unique identifier of the machine.
        sensor_name: Name of the sensor to query.
        lookback_minutes: Historical period to retrieve (default: 60).
        bucket_interval_minutes: Time bucket interval in minutes (default: 5).
        db: Database connection from dependency injection.

    Returns:
        List of aggregated sensor data points.

    Raises:
        HTTPException: If validation fails, database query fails, or no data is found.
    """
    # Validate time parameters
    if lookback_minutes <= 0 or bucket_interval_minutes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time parameters must be strictly positive integers.",
        )

    if bucket_interval_minutes > lookback_minutes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bucket interval cannot exceed the lookback period.",
        )

    query = """
        SELECT 
            time_bucket($1 * INTERVAL '1 minute', time) AS timestamp,
            machine_id,
            sensor_name,
            AVG(value) AS average_value,
            MIN(value) AS min_value,
            MAX(value) AS max_value
        FROM sensor_data
        WHERE machine_id = $2 
          AND sensor_name = $3
          AND time > NOW() - ($4 * INTERVAL '1 minute')
        GROUP BY timestamp, machine_id, sensor_name
        ORDER BY timestamp DESC;
    """

    try:
        rows = await db.fetch(
            query,
            bucket_interval_minutes,
            machine_id,
            sensor_name,
            lookback_minutes,
        )
    except Exception as e:
        logger.error(
            f"Database query failed for machine_id={machine_id}, "
            f"sensor_name={sensor_name}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error.",
        )

    if not rows:
        logger.warning(
            f"No data found for machine_id={machine_id}, sensor_name={sensor_name}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for machine '{machine_id}' and sensor '{sensor_name}'.",
        )

    return [SensorAggregatedResponse(**dict(row)) for row in rows]