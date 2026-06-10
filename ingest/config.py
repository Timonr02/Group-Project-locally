import os
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class ModuleConfig:
    """Configuration for a single OPC UA module."""
    
    def __init__(self, name: str, config_dict: Dict[str, Any]) -> None:
        self.name = name
        self.url = config_dict.get("url")
        self.table_name = config_dict.get("table_name")
        self.nodes = config_dict.get("nodes", {})
        
        if not self.url or not self.table_name:
            raise ValueError(f"Module '{name}' missing 'url' or 'table_name'")

class AppConfig:
    """Manages application configuration via environment variables and mapping file."""
    
    def __init__(self) -> None:
        self.db_dsn = os.getenv("DB_DSN", "postgresql://postgres:postgres@localhost:5433/postgres")
        self.mqtt_host = os.getenv("MQTT_HOST", "localhost")
        self.mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        self.subscription_interval_ms = int(os.getenv("SUBSCRIPTION_INTERVAL_MS", "500"))
        
        self.modules = self._load_modules("mapping.json")

    def _load_modules(self, filepath: str) -> Dict[str, ModuleConfig]:
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                mapping_data = json.load(file)
                modules = {}
                for module_name, module_config in mapping_data.get("modules", {}).items():
                    modules[module_name] = ModuleConfig(module_name, module_config)
                    logger.info(f"Loaded module: {module_name} from {module_config.get('url')}")
                return modules
        except FileNotFoundError:
            logger.error(f"Mapping file '{filepath}' not found.")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse mapping JSON: {e}")
            return {}
        except ValueError as e:
            logger.error(f"Invalid module config: {e}")
            return {}