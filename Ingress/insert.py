import asyncio
import json
import logging
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import paho.mqtt.client as mqtt
import psycopg2
from asyncua import Client
from asyncua.common.node import Node

logger = logging.getLogger(__name__)

DEFAULT_DB_DSN = "dbname='postgres' user='postgres' password='password' host='localhost' port='5433'"
DEFAULT_MQTT_HOST = "localhost"
DEFAULT_MQTT_PORT = 1883
DEFAULT_OPCUA_URL = "opc.tcp://0.0.0.0:4840/laser/"
DEFAULT_SUBSCRIPTION_INTERVAL_MS = 500


@dataclass
class SensorData:
    """Data structure for sensor readings.

    Attributes:
        timestamp: UTC timestamp of the measurement.
        machine_id: Unique identifier of the machine.
        sensor_name: Name of the sensor.
        value: Measured value.
    """

    timestamp: datetime
    machine_id: str
    sensor_name: str
    value: float


class DataProcessor:
    """Process and validate raw OPC UA sensor data.

    Handles value cleaning, metadata extraction, and timestamp normalization
    from multiple timestamp sources.
    """

    def __init__(self, node_mapping: Dict[str, Tuple[str, str]]) -> None:
        """Initialize the data processor.

        Args:
            node_mapping: Dictionary mapping OPC UA node IDs to (machine_id, sensor_name) tuples.
        """
        self.node_mapping = node_mapping

    def process(
        self,
        node_id: str,
        raw_value: Any,
        source_ts: Any,
        server_ts: Any,
    ) -> Optional[SensorData]:
        """Process raw OPC UA data into validated SensorData.

        Args:
            node_id: OPC UA node identifier.
            raw_value: Raw sensor value (may be invalid).
            source_ts: Source timestamp from OPC UA.
            server_ts: Server timestamp from OPC UA.

        Returns:
            Validated SensorData if value is valid, None otherwise.
        """
        clean_val = self._clean_value(raw_value)
        if clean_val is None:
            return None

        machine_id, sensor_name = self._get_metadata(node_id)
        timestamp = self._normalize_timestamp(source_ts, server_ts)

        return SensorData(timestamp, machine_id, sensor_name, clean_val)

    def _clean_value(self, raw_value: Any) -> Optional[float]:
        """Validate and convert raw value to float.

        Args:
            raw_value: Raw value from OPC UA.

        Returns:
            Cleaned float value, or None if invalid (NaN, Inf, conversion error).
        """
        try:
            val = float(raw_value)
            if math.isnan(val) or math.isinf(val):
                logger.warning(f"Invalid value detected (NaN or Inf): {raw_value}")
                return None
            return val
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert value to float: {raw_value} ({e})")
            return None

    def _normalize_timestamp(self, source_ts: Any, server_ts: Any) -> datetime:
        """Normalize timestamp from multiple sources to UTC.

        Priority: source_ts > server_ts > current UTC time.

        Args:
            source_ts: Source timestamp from OPC UA.
            server_ts: Server timestamp from OPC UA.

        Returns:
            UTC-aware datetime object.
        """
        ts = source_ts or server_ts or datetime.now(timezone.utc)
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)

    def _get_metadata(self, node_id: str) -> Tuple[str, str]:
        """Extract machine_id and sensor_name from node mapping.

        Args:
            node_id: OPC UA node identifier.

        Returns:
            Tuple of (machine_id, sensor_name). Returns fallback values if not found.
        """
        return self.node_mapping.get(node_id, ("unknown_machine", "unknown_sensor"))


class DatabaseManager:
    """Manage PostgreSQL/TimescaleDB connection and operations.

    Handles schema initialization and sensor data insertion.
    """

    def __init__(self, dsn: str) -> None:
        """Initialize the database manager.

        Args:
            dsn: PostgreSQL connection string.
        """
        self.dsn = dsn
        self.conn = None

    def connect(self) -> None:
        """Establish database connection.

        Raises:
            psycopg2.Error: If connection fails.
        """
        try:
            self.conn = psycopg2.connect(self.dsn)
            self.conn.autocommit = True
            logger.info("Database connection established")
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def setup_schema(self) -> None:
        """Create sensor_data table and configure TimescaleDB hypertable.

        Raises:
            psycopg2.Error: If schema setup fails.
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sensor_data (
                        time TIMESTAMPTZ NOT NULL,
                        machine_id VARCHAR(50) NOT NULL,
                        sensor_name VARCHAR(50) NOT NULL,
                        value DOUBLE PRECISION
                    );
                """)
                cur.execute(
                    "SELECT create_hypertable('sensor_data', 'time', if_not_exists => TRUE);"
                )
            logger.info("Database schema initialized")
        except psycopg2.Error as e:
            logger.error(f"Failed to setup database schema: {e}")
            raise

    def insert(self, data: SensorData) -> None:
        """Insert sensor data into the database.

        Args:
            data: SensorData object to insert.

        Raises:
            psycopg2.Error: If insertion fails.
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO sensor_data (time, machine_id, sensor_name, value) VALUES (%s, %s, %s, %s)",
                    (data.timestamp, data.machine_id, data.sensor_name, data.value),
                )
        except psycopg2.Error as e:
            logger.error(f"Failed to insert sensor data: {e}")
            raise

    def close(self) -> None:
        """Close database connection."""
        if self.conn is not None:
            try:
                self.conn.close()
                logger.info("Database connection closed")
            except psycopg2.Error as e:
                logger.error(f"Error closing database connection: {e}")


class MqttManager:
    """Manage MQTT client connection and sensor data publishing."""

    def __init__(self, host: str, port: int) -> None:
        """Initialize the MQTT manager.

        Args:
            host: MQTT broker hostname.
            port: MQTT broker port.
        """
        self.host = host
        self.port = port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._setup_callbacks()

    def _setup_callbacks(self) -> None:
        """Configure MQTT client callbacks."""
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish

    def _on_connect(self, client: mqtt.Client, userdata: Any, connect_flags: Any, rc: int, properties: Any) -> None:
        """Handle MQTT connection event."""
        if rc == 0:
            logger.info("MQTT client connected successfully")
        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, disconnect_flags: Any, rc: int, properties: Any) -> None:
        """Handle MQTT disconnection event."""
        if rc == 0:
            logger.info("MQTT client disconnected cleanly")
        else:
            logger.warning(f"MQTT client disconnected unexpectedly (code {rc})")

    def _on_publish(self, client: mqtt.Client, userdata: Any, mid: int, reason_codes: Any, properties: Any) -> None:
        """Handle MQTT publish confirmation."""
        logger.debug(f"MQTT message published (mid={mid})")

    def connect(self) -> None:
        """Connect to MQTT broker.

        Raises:
            mqtt.MQTTException: If connection fails.
        """
        try:
            self.client.connect(self.host, self.port, keepalive=60)
            self.client.loop_start()
            logger.info(f"MQTT connection initiated to {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise

    def publish(self, data: SensorData) -> None:
        """Publish sensor data to MQTT topic.

        Args:
            data: SensorData object to publish.
        """
        topic = f"factory/{data.machine_id}/{data.sensor_name}"
        payload = json.dumps(
            {
                "timestamp": data.timestamp.isoformat(),
                "value": data.value,
            }
        )
        try:
            self.client.publish(topic, payload, qos=1)
            logger.debug(f"Published to {topic}: {payload}")
        except Exception as e:
            logger.error(f"Failed to publish to MQTT: {e}")

    def close(self) -> None:
        """Close MQTT connection."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT connection closed")
        except Exception as e:
            logger.error(f"Error closing MQTT connection: {e}")


class OpcuaSubscriptionHandler:
    """Handle OPC UA data change notifications.

    Processes incoming sensor data from OPC UA subscriptions and routes it
    to database and MQTT broker.
    """

    def __init__(
        self,
        processor: DataProcessor,
        db: DatabaseManager,
        mqtt_mgr: MqttManager,
    ) -> None:
        """Initialize the OPC UA subscription handler.

        Args:
            processor: DataProcessor instance for value validation.
            db: DatabaseManager instance for persistence.
            mqtt_mgr: MqttManager instance for publishing.
        """
        self.processor = processor
        self.db = db
        self.mqtt_mgr = mqtt_mgr

    def datachange_notification(self, node: Node, val: Any, data: Any) -> None:
        """Handle OPC UA data change notification.

        Args:
            node: OPC UA node that changed.
            val: New value from the node.
            data: Additional notification data.
        """
        node_id = node.nodeid.to_string()

        dv = data.monitored_item.Value
        source_ts = getattr(dv, "SourceTimestamp", None)
        server_ts = getattr(dv, "ServerTimestamp", None)

        sensor_data = self.processor.process(node_id, val, source_ts, server_ts)

        if not sensor_data:
            return

        try:
            self.db.insert(sensor_data)
            self.mqtt_mgr.publish(sensor_data)
            logger.info(
                f"Data ingested: {sensor_data.machine_id} | "
                f"{sensor_data.sensor_name} = {sensor_data.value}"
            )
        except Exception as e:
            logger.error(f"Failed to process sensor data: {e}")


async def main() -> None:
    """Main entry point for the ingress service.

    Initializes all components, establishes OPC UA subscription,
    and processes data until interrupted.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    db_dsn = os.getenv("DB_DSN", DEFAULT_DB_DSN)
    mqtt_host = os.getenv("MQTT_HOST", DEFAULT_MQTT_HOST)
    mqtt_port = int(os.getenv("MQTT_PORT", DEFAULT_MQTT_PORT))
    opcua_url = os.getenv("OPCUA_URL", DEFAULT_OPCUA_URL)

    logger.info("Starting ingress service")
    logger.debug(f"Configuration: MQTT={mqtt_host}:{mqtt_port}, OPC UA={opcua_url}")

    db = DatabaseManager(db_dsn)
    db.connect()
    db.setup_schema()

    mqtt_mgr = MqttManager(mqtt_host, mqtt_port)
    mqtt_mgr.connect()

    try:
        async with Client(url=opcua_url) as opc_client:
            logger.info("Connected to OPC UA server")
            nsidx = await opc_client.get_namespace_index("laser_module")

            node_progress = await opc_client.nodes.root.get_child(
                ["0:Objects", f"{nsidx}:status", f"{nsidx}:progress"]
            )
            node_duration = await opc_client.nodes.root.get_child(
                ["0:Objects", f"{nsidx}:status", f"{nsidx}:last_job_duration_s"]
            )
            node_cards = await opc_client.nodes.root.get_child(
                ["0:Objects", f"{nsidx}:status", f"{nsidx}:count_finished_card"]
            )

            node_mapping = {
                node_progress.nodeid.to_string(): ("laser_01", "progress"),
                node_duration.nodeid.to_string(): ("laser_01", "last_job_duration_s"),
                node_cards.nodeid.to_string(): ("laser_01", "count_finished_card"),
            }

            processor = DataProcessor(node_mapping)
            handler = OpcuaSubscriptionHandler(processor, db, mqtt_mgr)

            subscription = await opc_client.create_subscription(
                DEFAULT_SUBSCRIPTION_INTERVAL_MS, handler
            )
            await subscription.subscribe_data_change([node_progress, node_duration, node_cards])

            logger.info("OPC UA subscription active, listening for data changes")
            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info("Received cancellation signal")
            finally:
                await subscription.delete()
                logger.info("Subscription deleted")

    except Exception as e:
        logger.error(f"Fatal error in ingress service: {e}", exc_info=True)
        raise
    finally:
        db.close()
        mqtt_mgr.close()
        logger.info("Ingress service shut down complete")


if __name__ == "__main__":
    asyncio.run(main())