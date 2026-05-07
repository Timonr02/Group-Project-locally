from fastapi import APIRouter, Depends, HTTPException, status
from asyncpg import Pool
from typing import List

from models import SensorAggregatedResponse
from database import DatabasePoolManager

router = APIRouter(prefix="/api/v1", tags=["Sensor Data"])

async def get_db_connection():
    pool = await DatabasePoolManager.get_pool()
    async with pool.acquire() as connection:
        yield connection
@router.get(
    "/machines/{machine_id}/sensors/{sensor_name}",
    response_model=List[SensorAggregatedResponse],
    summary="Retrieve aggregated sensor data",
    description="""
    Fetches historical sensor data from the TimescaleDB replica node. 
    The data is automatically aggregated into time buckets.
    """
)
async def get_aggregated_sensor_data(
    machine_id: str,
    sensor_name: str,
    lookback_minutes: int = 60,
    bucket_interval_minutes: int = 5,
    db: Pool = Depends(get_db_connection)
):
    # Guard Clauses
    if lookback_minutes <= 0 or bucket_interval_minutes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time parameters must be strictly positive integers."
        )

    if bucket_interval_minutes > lookback_minutes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bucket interval cannot exceed the lookback period."
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
            lookback_minutes
        )
    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Database Error")

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for machine '{machine_id}' and sensor '{sensor_name}'."
        )

    return [dict(row) for row in rows]