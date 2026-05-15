import os
import json
import logging
from typing import Dict, Tuple
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class AppConfig:
    """Manages application configuration via environment variables."""

    def __init__(self) -> None:
        self.db_dsn = os.getenv("DB_DSN", "postgresql://postgres:postgres@localhost:5433/postgres")
        self.mqtt_host = os.getenv("MQTT_HOST", "localhost")
        self.mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        self.opcua_url = os.getenv("OPCUA_URL", "opc.tcp://127.0.0.1:4840/laser/")
        self.node_mapping = self._parse_node_mapping(os.getenv("NODE_MAPPING", "{}"))

    def _parse_node_mapping(self, mapping_json: str) -> Dict[str, Tuple[str, str]]:
        try:
            raw_mapping = json.loads(mapping_json)
            return {str(k): (str(v[0]), str(v[1])) for k, v in raw_mapping.items()}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse NODE_MAPPING: {e}")
            return {}