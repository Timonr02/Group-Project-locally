from datetime import datetime
from pydantic import BaseModel, Field

class SensorAggregatedResponse(BaseModel):
    timestamp: datetime = Field(description="Start time of the aggregated bucket")
    machine_id: str = Field(description="Unique identifier of the machine")
    sensor_name: str = Field(description="Name of the sensor")
    average_value: float = Field(description="Averaged value within the time bucket")
    min_value: float = Field(description="Minimum value within the time bucket")
    max_value: float = Field(description="Maximum value within the time bucket")