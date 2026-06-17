CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS laser_data (
    time TIMESTAMPTZ NOT NULL,
    sensor_name TEXT NOT NULL,
    value DOUBLE PRECISION,
    PRIMARY KEY (time, sensor_name)
);
SELECT create_hypertable('laser_data', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_laser_data_sensor_time 
ON laser_data (sensor_name, time DESC);

CREATE TABLE IF NOT EXISTS delta_robot_data(
    time TIMESTAMPTZ NOT NULL,
    sensor_name TEXT NOT NULL,
    value DOUBLE PRECISION,
    PRIMARY KEY (time, sensor_name)
);

SELECT create_hypertable('delta_robot_data', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_delta_robot_sensor_time
ON delta_robot_data (sensor_name, time DESC);

CREATE TABLE IF NOT EXISTS cmms_data (
    time TIMESTAMPTZ NOT NULL,
    machine_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    value DOUBLE PRECISION,
    PRIMARY KEY (time, machine_id, metric_name)
);
CREATE INDEX IF NOT EXISTS idx_cmms_machine_time 
ON cmms_data (machine_id, time DESC);

CREATE TABLE IF NOT EXISTS machine_events (
    time TIMESTAMPTZ NOT NULL,
    machine_id VARCHAR(50) NOT NULL,
    event_name VARCHAR(50) NOT NULL,
    message TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_machine_events_lookup 
ON machine_events (machine_id, event_name, time DESC);