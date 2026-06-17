import json
import logging
import paho.mqtt.client as mqtt
from models import SensorData

logger = logging.getLogger(__name__)

class MqttManager:
    """Manages MQTT broker connection and data publishing with debug callbacks."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish

    def connect(self) -> None:
        try:
            self.client.connect(self.host, self.port, keepalive=60)
            self.client.loop_start()
            logger.info(f"MQTT connection attempt initiated to {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"MQTT connection setup failed: {e}")
            raise

    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        if reason_code == 0:
            logger.info("MQTT Connection established successfully! 🎉")
        else:
            logger.error(f"MQTT Connection refused by broker. Reason code: {reason_code}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties) -> None:
        logger.warning(f"MQTT disconnected from broker. Reason code: {reason_code}")

    def _on_publish(self, client, userdata, mid, reason_code, properties) -> None:
        logger.debug(f"MQTT message published successfully. Message ID: {mid}")

    def publish(self, data: SensorData, module_name: str = "default") -> None:
        topic = f"factory/{module_name}/{data.sensor_name}"
        payload = json.dumps({
            "timestamp": data.timestamp.isoformat(),
            "value": data.value,
        })
        try:
            info = self.client.publish(topic, payload, qos=1)
            logger.info(f"[{module_name}] Published MQTT topic: {topic} | Mid: {info.mid}")
        except Exception as e:
            logger.error(f"MQTT publish failed for topic {topic}: {e}")

    def close(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT connection closed")