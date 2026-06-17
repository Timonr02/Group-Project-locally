from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class SensorData:
    """Data structure representing a single sensor reading or machine event."""
    timestamp: datetime
    sensor_name: str
    value: Any
    hot_path: bool = False