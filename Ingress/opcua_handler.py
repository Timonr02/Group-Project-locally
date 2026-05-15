import logging
from typing import Any
from asyncua.common.node import Node
from processor import DataProcessor
from database import DatabaseManager
from mqtt import MqttManager

logger = logging.getLogger(__name__)

class OpcuaSubscriptionHandler:
    """Handles incoming data change events from the OPC UA subscription."""

    def __init__(self, processor: DataProcessor, db: DatabaseManager, mqtt_mgr: MqttManager) -> None:
        self.processor = processor
        self.db = db
        self.mqtt_mgr = mqtt_mgr

    def datachange_notification(self, node: Node, val: Any, data: Any) -> None:
        node_id = node.nodeid.to_string()
        monitored_value = data.monitored_item.Value
        source_ts = getattr(monitored_value, "SourceTimestamp", None)
        server_ts = getattr(monitored_value, "ServerTimestamp", None)

        sensor_data = self.processor.process(node_id, val, source_ts, server_ts)

        if sensor_data:
            self.db.insert(sensor_data)
            self.mqtt_mgr.publish(sensor_data)
            logger.info(f"Ingested: {sensor_data.machine_id} | {sensor_data.sensor_name} -> {sensor_data.value}")