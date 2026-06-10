from dataclasses import dataclass
from datetime import datetime

@dataclass
class SensorData:
    """Data structure representing a single sensor reading."""
    timestamp: datetime
    sensor_name: str
    value: float
    hot_path: bool = False