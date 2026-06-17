from datetime import datetime
from typing import Optional, List
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


class SensorMetric(BaseModel):
    """Response model for raw sensor metrics."""

    timestamp: datetime = Field(..., description="UTC timestamp of the measurement")
    sensor_name: str = Field(..., description="Name of the sensor")
    value: float = Field(..., description="Sensor value")


class MetricsResponse(BaseModel):
    """Response model for metrics query endpoint."""

    metrics: List[SensorMetric] = Field(..., description="List of sensor metrics")
    count: int = Field(..., description="Total number of metrics returned")
    query_params: dict = Field(..., description="Echo of the query parameters used")


class MachineEvent(BaseModel):
    """Response model for a single machine text event (logs, errors)."""
    timestamp: datetime = Field(..., description="UTC timestamp of the event")
    event_name: str = Field(..., description="Name of the event / log type")
    message: str = Field(..., description="The text message or description")


class EventsResponse(BaseModel):
    """Response model for the events query endpoint."""
    events: List[MachineEvent] = Field(..., description="List of text events")
    count: int = Field(..., description="Total number of events returned")
    query_params: dict = Field(..., description="Echo of query parameters")


class CMMSDataInsert(BaseModel):
    """Request model for CMMS data."""

    machine_id: str
    metric_name: str
    value: float
    timestamp: Optional[datetime] = None


class CMMSDataResponse(BaseModel):
    """Response model for single CMMS data entry."""

    time: datetime
    machine_id: str
    metric_name: str
    value: float


class CMMSMetricsResponse(BaseModel):
    """Response model for CMMS metrics query."""
    metrics: List[CMMSDataResponse] = Field(..., description="List of CMMS metrics")
    count: int = Field(..., description="Total number of entries returned")