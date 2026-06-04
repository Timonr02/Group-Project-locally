import math
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Tuple, Optional
from models import SensorData

logger = logging.getLogger(__name__)

class DataProcessor:
    """Processes, cleans, and normalizes raw OPC UA data for a specific module."""

    def __init__(self, module_name: str, node_mapping: Dict[str, Tuple[str, str]]) -> None:
        self.module_name = module_name
        self.node_mapping = node_mapping

    def process(self, node_id: str, raw_value: Any, source_ts: Any, server_ts: Any) -> Optional[SensorData]:
        cleaned_value = self._clean_value(raw_value)
        if cleaned_value is None:
            return None

        machine_id, sensor_name = self._get_metadata(node_id)
        timestamp = self._normalize_timestamp(source_ts, server_ts)

        return SensorData(timestamp, machine_id, sensor_name, cleaned_value)

    def _clean_value(self, raw_value: Any) -> Optional[float]:
        """Convert raw OPC UA values to float. Skip lists, dicts, complex objects, convert bools to 1.0/0.0, and try numeric conversion."""
        if raw_value is None:
            return None
        
        if isinstance(raw_value, (list, dict)) or (hasattr(raw_value, '__dict__') and not isinstance(raw_value, (bool, int, float))):
            return None
        
        if isinstance(raw_value, bool):
            return 1.0 if raw_value else 0.0
        
        try:
            val = float(raw_value)
            if math.isnan(val) or math.isinf(val):
                return None
            return val
        except (ValueError, TypeError):
            return None

    def _normalize_timestamp(self, source_ts: Any, server_ts: Any) -> datetime:
        ts = source_ts or server_ts or datetime.now(timezone.utc)
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)

    def _get_metadata(self, node_id: str) -> Tuple[str, str]:
        return self.node_mapping.get(node_id, ("unknown_machine", "unknown_sensor"))