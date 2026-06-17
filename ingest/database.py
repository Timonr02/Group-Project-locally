import logging
import psycopg2
from models import SensorData

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages PostgreSQL connection for data insertion with automatic routing."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self.conn = None

    def connect(self) -> None:
        """Connect to PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(self.dsn)
            self.conn.autocommit = True
            logger.info("Database connection established")
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def insert(self, data: SensorData, table_name: str) -> None:
        """Insert sensor data into the specified table or route to machine_events if it is a string."""
        if not self.conn:
            return

        try:
            with self.conn.cursor() as cur:
                if isinstance(data.value, str):
                    machine_id = table_name.replace("_data", "")
                    cur.execute(
                        "INSERT INTO machine_events (time, machine_id, event_name, message) VALUES (%s, %s, %s, %s)",
                        (data.timestamp, machine_id, data.sensor_name, data.value),
                    )
                else:
                    cur.execute(
                        f"INSERT INTO {table_name} (time, sensor_name, value) VALUES (%s, %s, %s)",
                        (data.timestamp, data.sensor_name, data.value),
                    )
        except psycopg2.Error as e:
            logger.error(f"Data insertion failed for {table_name}: {e}")

    def close(self) -> None:
        """Close database connection."""
        if self.conn is not None:
            self.conn.close()
            logger.info("Database connection closed")