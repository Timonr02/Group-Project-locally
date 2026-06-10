import asyncio
import logging
from asyncua import Client

from config import AppConfig, ModuleConfig
from database import DatabaseManager
from mqtt import MqttManager
from processor import DataProcessor
from opcua_handler import OpcuaSubscriptionHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class IngestionService:
    """Orchestrates the data ingestion pipeline from multiple OPC UA sources to PostgreSQL and MQTT."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.db = DatabaseManager(self.config.db_dsn)
        self.mqtt_mgr = MqttManager(self.config.mqtt_host, self.config.mqtt_port)

    async def run(self) -> None:
        self.db.connect()
        
        self.mqtt_mgr.connect()

        tasks = []
        for module_name, module_config in self.config.modules.items():
            task = asyncio.create_task(self._manage_opcua_session(module_name, module_config))
            tasks.append(task)

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Service stopped manually.")
        finally:
            self.db.close()
            self.mqtt_mgr.close()

    async def _manage_opcua_session(self, module_name: str, module_config: ModuleConfig) -> None:
        """Manage OPC UA connection for a specific module with automatic reconnection."""
        while True:
            try:
                logger.info(f"[{module_name}] Connecting to OPC UA Server: {module_config.url}")
                async with Client(url=module_config.url) as opc_client:
                    logger.info(f"[{module_name}] OPC UA connection established")
                    
                    processor = DataProcessor(module_name, module_config.nodes)
                    handler = OpcuaSubscriptionHandler(module_name, module_config.table_name, processor, self.db, self.mqtt_mgr)
                    
                    subscription = await opc_client.create_subscription(self.config.subscription_interval_ms, handler)
                    
                    for node_id in module_config.nodes.keys():
                        try:
                            node = opc_client.get_node(node_id)
                            await subscription.subscribe_data_change(node)
                            logger.info(f"[{module_name}] Subscribed to node: {node_id}")
                        except Exception as e:
                            logger.warning(f"[{module_name}] Could not subscribe to {node_id}: {e}")

                    while True:
                        await asyncio.sleep(1)

            except asyncio.CancelledError:
                logger.info(f"[{module_name}] Connection task cancelled.")
                break
            except Exception as e:
                logger.error(f"[{module_name}] Connection lost: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)

if __name__ == "__main__":
    config = AppConfig()
    
    if not config.modules:
        logger.error("No modules configured in mapping.json")
        exit(1)
    
    service = IngestionService(config)
    try:
        asyncio.run(service.run())
    except KeyboardInterrupt:
        logger.info("Service interrupted by user.")