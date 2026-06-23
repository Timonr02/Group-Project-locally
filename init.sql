CREATE EXTENSION IF NOT EXISTS timescaledb;


DROP MATERIALIZED VIEW IF EXISTS laser_5min_avg CASCADE;
DROP MATERIALIZED VIEW IF EXISTS delta_robot_5min_avg CASCADE;

DROP VIEW IF EXISTS calc_oee CASCADE;
DROP VIEW IF EXISTS machine_oee CASCADE;

DROP TABLE IF EXISTS machine_events CASCADE;
DROP TABLE IF EXISTS laser_data CASCADE;
DROP TABLE IF EXISTS delta_robot_data CASCADE;
DROP TABLE IF EXISTS cmms_data CASCADE;
DROP TABLE IF EXISTS sensor_data CASCADE;


CREATE TABLE laser_data (

    time TIMESTAMPTZ NOT NULL,
    sensor_name TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (time, sensor_name)
);

SELECT create_hypertable(
    'laser_data',
    'time',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_laser_sensor
ON laser_data(sensor_name);

ALTER TABLE laser_data
SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'sensor_name'
);

SELECT add_compression_policy(
    'laser_data',
    INTERVAL '2 days'
);

SELECT add_retention_policy(
    'laser_data',
    INTERVAL '30 days'
);



CREATE TABLE delta_robot_data (
    time TIMESTAMPTZ NOT NULL,
    sensor_name TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (time, sensor_name)
);

SELECT create_hypertable(
    'delta_robot_data',
    'time',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_delta_robot_sensor
ON delta_robot_data(sensor_name);

ALTER TABLE delta_robot_data
SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'sensor_name'
);

SELECT add_compression_policy(
    'delta_robot_data',
    INTERVAL '2 days'
);

SELECT add_retention_policy(
    'delta_robot_data',
    INTERVAL '30 days'
);



CREATE TABLE cmms_data (
    time TIMESTAMPTZ NOT NULL,
    machine_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    value DOUBLE PRECISION,
    PRIMARY KEY (time, machine_id, metric_name)
);

CREATE INDEX IF NOT EXISTS idx_cmms_machine_time
ON cmms_data (machine_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_cmms_machine
ON cmms_data(machine_id);

CREATE INDEX IF NOT EXISTS idx_cmms_metric
ON cmms_data(metric_name);



CREATE TABLE machine_events (
    time TIMESTAMPTZ NOT NULL,
    machine_id TEXT NOT NULL,
    event_name TEXT NOT NULL,
    message TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_machine_events_lookup
ON machine_events (machine_id, event_name, time DESC);



CREATE VIEW machine_oee AS

WITH latest AS (
    SELECT DISTINCT ON (machine_id, metric_name)
        machine_id,
        metric_name,
        value
    FROM cmms_data
    ORDER BY machine_id, metric_name, time DESC
),

data AS (
    SELECT
        machine_id,

        MAX(value) FILTER (
            WHERE metric_name = 'LastCycleTime'
        ) AS last_cycle_time,

        MAX(value) FILTER (
            WHERE metric_name = 'AverageCycleTime'
        ) AS average_cycle_time,

        MAX(value) FILTER (
            WHERE metric_name = 'ActualOperatingTime'
        ) AS actual_operating_time,

        MAX(value) FILTER (
            WHERE metric_name = 'PlannedProductionTime'
        ) AS planned_production_time,

        MAX(value) FILTER (
            WHERE metric_name = 'IdealCycleTime'
        ) AS ideal_cycle_time,

        MAX(value) FILTER (
            WHERE metric_name = 'GoodParts'
        ) AS good_parts,

        MAX(value) FILTER (
            WHERE metric_name = 'BadParts'
        ) AS bad_parts

    FROM latest
    GROUP BY machine_id
),

calc AS (
    SELECT
        machine_id,

        last_cycle_time,
        average_cycle_time,
        actual_operating_time,
        planned_production_time,
        ideal_cycle_time,
        good_parts,
        bad_parts,

        good_parts + bad_parts AS total_parts_produced,

        (
            (last_cycle_time - average_cycle_time)
            / NULLIF(average_cycle_time, 0)
        ) * 100 AS time_deviation_percentage,

        (
            actual_operating_time
            / NULLIF(planned_production_time, 0)
        ) * 100 AS availability_percentage,

        (
            ((good_parts + bad_parts) * ideal_cycle_time)
            / NULLIF(actual_operating_time, 0)
        ) * 100 AS performance_percentage,

        (
            good_parts
            / NULLIF(good_parts + bad_parts, 0)
        ) * 100 AS quality_percentage

    FROM data
)

SELECT
    machine_id,

    last_cycle_time,
    average_cycle_time,
    actual_operating_time,
    planned_production_time,
    ideal_cycle_time,
    good_parts,
    bad_parts,
    total_parts_produced,

    time_deviation_percentage,
    availability_percentage,
    performance_percentage,
    quality_percentage,

    (
        availability_percentage
        * performance_percentage
        * quality_percentage
    ) / 10000 AS oee_percentage

FROM calc;



CREATE OR REPLACE VIEW calc_oee AS
SELECT
    machine_id,
    availability_percentage,
    performance_percentage,
    quality_percentage,

    (
        availability_percentage
        * performance_percentage
        * quality_percentage
    ) / 10000 AS calc_oee

FROM machine_oee;



CREATE MATERIALIZED VIEW laser_5min_avg
WITH (timescaledb.continuous) AS

SELECT
    time_bucket('5 minutes', time) AS bucket,
    sensor_name,

    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    COUNT(*) AS total_rows

FROM laser_data

GROUP BY
    bucket,
    sensor_name

WITH NO DATA;

SELECT add_continuous_aggregate_policy(
    'laser_5min_avg',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute'
);

CALL refresh_continuous_aggregate(
    'laser_5min_avg',
    NOW() - INTERVAL '1 hour',
    NOW()
);



CREATE MATERIALIZED VIEW delta_robot_5min_avg
WITH (timescaledb.continuous) AS

SELECT
    time_bucket('5 minutes', time) AS bucket,
    sensor_name,

    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    COUNT(*) AS total_rows

FROM delta_robot_data

GROUP BY
    bucket,
    sensor_name

WITH NO DATA;

SELECT add_continuous_aggregate_policy(
    'delta_robot_5min_avg',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute'
);

CALL refresh_continuous_aggregate(
    'delta_robot_5min_avg',
    NOW() - INTERVAL '1 hour',
    NOW()
);


DO $$
BEGIN

IF NOT EXISTS (
    SELECT
    FROM pg_roles
    WHERE rolname = 'ingest_role'
) THEN
    CREATE ROLE ingest_role
    LOGIN
    PASSWORD 'ingest123';
END IF;

IF NOT EXISTS (
    SELECT
    FROM pg_roles
    WHERE rolname = 'egress_role'
) THEN
    CREATE ROLE egress_role
    LOGIN
    PASSWORD 'egress123';
END IF;

IF NOT EXISTS (
    SELECT
    FROM pg_roles
    WHERE rolname = 'grafana_role'
) THEN
    CREATE ROLE grafana_role
    LOGIN
    PASSWORD 'grafana123';
END IF;

END $$;


GRANT INSERT ON machine_events TO ingest_role;
GRANT SELECT, INSERT ON machine_events TO egress_role;
GRANT SELECT ON machine_events TO grafana_role;

GRANT INSERT ON laser_data TO ingest_role;
GRANT SELECT, INSERT ON laser_data TO egress_role;
GRANT SELECT ON laser_data TO grafana_role;

GRANT INSERT ON delta_robot_data TO ingest_role;
GRANT SELECT, INSERT ON delta_robot_data TO egress_role;
GRANT SELECT ON delta_robot_data TO grafana_role;

GRANT INSERT ON cmms_data TO ingest_role;
GRANT SELECT, INSERT ON cmms_data TO egress_role;
GRANT SELECT ON cmms_data TO grafana_role;

GRANT SELECT ON laser_5min_avg TO grafana_role;
GRANT SELECT ON delta_robot_5min_avg TO grafana_role;

GRANT SELECT ON machine_oee TO grafana_role;
GRANT SELECT ON calc_oee TO grafana_role;

GRANT SELECT ON machine_oee TO egress_role;
GRANT SELECT ON calc_oee TO egress_role;


SELECT * FROM machine_oee;
SELECT * FROM calc_oee;
```
