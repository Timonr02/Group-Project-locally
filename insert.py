import asyncio
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from dotenv import load_dotenv
from typing import Dict, Tuple, Optional, Any

import paho.mqtt.client as mqtt
import psycopg2
from asyncua import Client
from asyncua.common.node import Node


@dataclass
class SensorData:
    timestamp: datetime
    machine_id: str
    sensor_name: str
    value: float

load_dotenv()

class DataProcessor:
    def __init__(self, node_mapping: Dict[str, Tuple[str, str]]):
        self.node_mapping = node_mapping

    def process(self, node_id: str, raw_value: Any, source_ts: Any, server_ts: Any) -> Optional[SensorData]:
        clean_val = self._clean_value(raw_value)
        if clean_val is None:
            return None

        machine_id, sensor_name = self._get_metadata(node_id)
        timestamp = self._normalize_timestamp(source_ts, server_ts)

        return SensorData(timestamp, machine_id, sensor_name, clean_val)

    def _clean_value(self, raw_value: Any) -> Optional[float]:
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


class DatabaseManager:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.conn = None

    def connect(self) -> None:
        self.conn = psycopg2.connect(self.dsn)
        self.conn.autocommit = True

    def setup_schema(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sensor_data (
                    time TIMESTAMPTZ NOT NULL,
                    machine_id VARCHAR(50) NOT NULL,
                    sensor_name VARCHAR(50) NOT NULL,
                    value DOUBLE PRECISION
                );
            """)
            cur.execute("SELECT create_hypertable('sensor_data', 'time', if_not_exists => TRUE);")

    def insert(self, data: SensorData) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO sensor_data (time, machine_id, sensor_name, value) VALUES (%s, %s, %s, %s)",
                (data.timestamp, data.machine_id, data.sensor_name, data.value)
            )

    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()


class MqttManager:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def connect(self) -> None:
        self.client.connect(self.host, self.port, 60)
        self.client.loop_start()

    def publish(self, data: SensorData) -> None:
        topic = f"factory/{data.machine_id}/{data.sensor_name}"
        payload = json.dumps({
            "timestamp": data.timestamp.isoformat(),
            "value": data.value
        })
        self.client.publish(topic, payload, qos=1)

    def close(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()


class OpcuaSubscriptionHandler:
    def __init__(self, processor: DataProcessor, db: DatabaseManager, mqtt_mgr: MqttManager):
        self.processor = processor
        self.db = db
        self.mqtt_mgr = mqtt_mgr

    def datachange_notification(self, node: Node, val: Any, data: Any) -> None:
        node_id = node.nodeid.to_string()
        
        dv = data.monitored_item.Value
        source_ts = getattr(dv, "SourceTimestamp", None)
        server_ts = getattr(dv, "ServerTimestamp", None)

        sensor_data = self.processor.process(node_id, val, source_ts, server_ts)
        
        if not sensor_data:
            return

        self.db.insert(sensor_data)
        self.mqtt_mgr.publish(sensor_data)


async def main() -> None:
    db_dsn = os.getenv("DB_DSN", "dbname='postgres' user='postgres' password='password' host='localhost' port='5433'")
    mqtt_host = os.getenv("MQTT_HOST", "localhost")
    mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
    opcua_url = os.getenv("OPCUA_URL", "opc.tcp://127.0.0.1:4840")
    
    node_mapping_raw = os.getenv("NODE_MAPPING", '{"ns=2;i=2": ["laser_01", "temperature"], "ns=2;i=3": ["laser_01", "power"]}')
    node_mapping = {k: tuple(v) for k, v in json.loads(node_mapping_raw).items()}

    db = DatabaseManager(db_dsn)
    db.connect()
    db.setup_schema()

    mqtt_mgr = MqttManager(mqtt_host, mqtt_port)
    mqtt_mgr.connect()

    processor = DataProcessor(node_mapping)
    handler = OpcuaSubscriptionHandler(processor, db, mqtt_mgr)

    async with Client(url=opcua_url) as opc_client:
        subscription = await opc_client.create_subscription(500, handler)
        
        for node_id in node_mapping.keys():
            node = opc_client.get_node(node_id)
            await subscription.subscribe_data_change(node)

        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await subscription.delete()
            db.close()
            mqtt_mgr.close()

if __name__ == "__main__":
    asyncio.run(main())