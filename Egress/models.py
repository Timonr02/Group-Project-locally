from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SensorAggregatedResponse(BaseModel):
    """Response model for aggregated sensor data."""

    timestamp: datetime = Field(..., description="Start time of the aggregated bucket")
    machine_id: str = Field(..., description="Unique identifier of the machine")
    sensor_name: str = Field(..., description="Name of the sensor")
    average_value: float = Field(..., description="Averaged value within the time bucket")
    min_value: float = Field(..., description="Minimum value within the time bucket")
    max_value: float = Field(..., description="Maximum value within the time bucket")


class SensorDataInsert(BaseModel):
    """Request model for inserting sensor data."""

    machine_id: str = Field(..., description="Unique identifier of the machine or asset")
    sensor_name: str = Field(..., description="Name of the sensor or generated metric")
    value: float = Field(..., description="The value to be stored")
    timestamp: Optional[datetime] = Field(
        default=None, description="Optional UTC timestamp. Defaults to now if omitted."
    )