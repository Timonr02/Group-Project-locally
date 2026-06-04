import logging
import psycopg2
from typing import List
from models import SensorData

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages PostgreSQL/TimescaleDB connection and schema operations for multiple modules."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self.conn = None
        self.module_tables: List[str] = []

    def connect(self) -> None:
        try:
            self.conn = psycopg2.connect(self.dsn)
            self.conn.autocommit = True
            logger.info("Database connection established")
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def setup_schema(self, module_table_names: List[str]) -> None:
        """Create tables for each module."""
        if not self.conn:
            raise RuntimeError("Database connection not initialized")
        
        self.module_tables = module_table_names

        with self.conn.cursor() as cur:
            for table_name in module_table_names:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        time TIMESTAMPTZ NOT NULL,
                        machine_id VARCHAR(50) NOT NULL,
                        sensor_name VARCHAR(50) NOT NULL,
                        value DOUBLE PRECISION
                    );
                """)
                
                try:
                    cur.execute(f"SELECT create_hypertable('{table_name}', 'time', if_not_exists => TRUE);")
                except psycopg2.Error as e:
                    logger.warning(f"Could not create hypertable for {table_name}: {e}")
                
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_machine_time 
                    ON {table_name} (machine_id, time DESC);
                """)
                logger.info(f"Schema created for table: {table_name}")

    def insert(self, data: SensorData, table_name: str) -> None:
        """Insert data into the specified module table."""
        if not self.conn:
            return

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {table_name} (time, machine_id, sensor_name, value) VALUES (%s, %s, %s, %s)",
                    (data.timestamp, data.machine_id, data.sensor_name, data.value),
                )
        except psycopg2.Error as e:
            logger.error(f"Data insertion failed for {table_name}: {e}")

    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()
            logger.info("Database connection closed")