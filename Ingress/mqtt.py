import json
import logging
import paho.mqtt.client as mqtt
from models import SensorData

logger = logging.getLogger(__name__)

class MqttManager:
    """Manages MQTT broker connection and data publishing."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def connect(self) -> None:
        try:
            self.client.connect(self.host, self.port, keepalive=60)
            self.client.loop_start()
            logger.info(f"MQTT connection established to {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            raise

    def publish(self, data: SensorData) -> None:
        topic = f"factory/{data.machine_id}/{data.sensor_name}"
        payload = json.dumps({
            "timestamp": data.timestamp.isoformat(),
            "value": data.value,
        })
        try:
            self.client.publish(topic, payload, qos=1)
        except Exception as e:
            logger.error(f"MQTT publish failed for topic {topic}: {e}")

    def close(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT connection closed")