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
        self.subscription_interval_ms = int(os.getenv("SUBSCRIPTION_INTERVAL_MS", "500"))
        
        self.node_paths = self._load_mapping_file("mapping.json")

    def _load_mapping_file(self, filepath: str) -> Dict[str, Tuple[str, str]]:
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                raw_mapping = json.load(file)
                return {str(k): (str(v[0]), str(v[1])) for k, v in raw_mapping.items()}
        except FileNotFoundError:
            logger.error(f"Mapping file '{filepath}' not found.")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse mapping JSON: {e}")
            return {}