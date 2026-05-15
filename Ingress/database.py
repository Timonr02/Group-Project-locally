import logging
import psycopg2
from models import SensorData

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages PostgreSQL/TimescaleDB connection and schema operations."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self.conn = None

    def connect(self) -> None:
        try:
            self.conn = psycopg2.connect(self.dsn)
            self.conn.autocommit = True
            logger.info("Database connection established")
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def setup_schema(self) -> None:
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

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
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_sensor_data_machine_time 
                ON sensor_data (machine_id, time DESC);
            """)

    def insert(self, data: SensorData) -> None:
        if not self.conn:
            return

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO sensor_data (time, machine_id, sensor_name, value) VALUES (%s, %s, %s, %s)",
                    (data.timestamp, data.machine_id, data.sensor_name, data.value),
                )
        except psycopg2.Error as e:
            logger.error(f"Data insertion failed: {e}")

    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()
            logger.info("Database connection closed")