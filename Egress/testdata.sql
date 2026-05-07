CREATE TABLE IF NOT EXISTS sensor_data (
    time TIMESTAMPTZ NOT NULL,
    machine_id VARCHAR(50) NOT NULL,
    sensor_name VARCHAR(50) NOT NULL,
    value DOUBLE PRECISION
);

DO $$ 
BEGIN 
    PERFORM create_hypertable('sensor_data', 'time', if_not_exists => TRUE);
EXCEPTION WHEN OTHERS THEN 
    RAISE NOTICE 'Hypertable exists already';
END $$;

TRUNCATE TABLE sensor_data;

INSERT INTO sensor_data (time, machine_id, sensor_name, value)
SELECT 
    generate_series(
        NOW() - INTERVAL '2 hours', 
        NOW(), 
        INTERVAL '1 minute'
    ) AS time,
    'laser_01' AS machine_id,
    'temperature' AS sensor_name,
    (25 + (random() * 5) + (EXTRACT(EPOCH FROM (age(NOW(), clock_timestamp()))) / 3600 * 20)) AS value;

INSERT INTO sensor_data (time, machine_id, sensor_name, value)
SELECT 
    generate_series(NOW() - INTERVAL '2 hours', NOW(), INTERVAL '10 minutes'),
    'laser_01',
    'is_running',
    (CASE WHEN random() > 0.2 THEN 1 ELSE 0 END);

SELECT * FROM sensor_data ORDER BY time DESC LIMIT 10;