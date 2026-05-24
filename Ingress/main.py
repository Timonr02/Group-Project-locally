import asyncio
import logging
from asyncua import Client

from config import AppConfig
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
    """Orchestrates the data ingestion pipeline from OPC UA to PostgreSQL and MQTT."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.db = DatabaseManager(self.config.db_dsn)
        self.mqtt_mgr = MqttManager(self.config.mqtt_host, self.config.mqtt_port)
        self.processor = DataProcessor(self.config.node_mapping)
        self.handler = OpcuaSubscriptionHandler(self.processor, self.db, self.mqtt_mgr)

    async def run(self) -> None:
        self.db.connect()
        self.db.setup_schema()
        self.mqtt_mgr.connect()

        while True:
            try:
                await self._manage_opcua_session()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Connection lost: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)

        self.db.close()
        self.mqtt_mgr.close()

    async def _manage_opcua_session(self) -> None:
        logger.info(f"Connecting to OPC UA Server: {self.config.opcua_url}")
        async with Client(url=self.config.opcua_url) as opc_client:
            logger.info("OPC UA connection established")

            dynamic_mapping = {}
            nodes_to_subscribe = []

            for path_str, (machine_id, sensor_name) in self.config.node_paths.items():
                try:
                    path_list = path_str.split("/")

                    node = await opc_client.nodes.root.get_child(path_list)

                    current_node_id = node.nodeid.to_string()

                    dynamic_mapping[current_node_id] = (machine_id, sensor_name)
                    nodes_to_subscribe.append(node)

                except Exception as e:
                    logger.warning(f"Could not find node at path {path_str}: {e}")

            self.processor.node_mapping = dynamic_mapping
            
            subscription = await opc_client.create_subscription(self.config.subscription_interval_ms, self.handler)

            for node in nodes_to_subscribe:
                await subscription.subscribe_data_change(node)
                logger.info(f"Subscribed to: {node.nodeid.to_string()}")

            while True:
                await asyncio.sleep(1)

if __name__ == "__main__":
    config = AppConfig()
    service = IngestionService(config)
    try:
        asyncio.run(service.run())
    except KeyboardInterrupt:
        logger.info("Service stopped manually.")