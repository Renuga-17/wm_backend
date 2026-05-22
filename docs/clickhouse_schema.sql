-- 1. Operational & Workflow Events Table (OLAP Audit Log)
CREATE TABLE IF NOT EXISTS warehouse_events (
    event_id UUID,
    event_type String,          -- 'SCAN_DOCK', 'PUTAWAY_ASSIGNED', 'PUTAWAY_CONFIRMED', 'PICK_CONFIRMED', etc.
    severity String,            -- 'INFO', 'WARNING', 'CRITICAL'
    timestamp DateTime64(3),
    warehouse_id UUID,
    zone_id Nullable(UUID),
    rack_id Nullable(UUID),
    bin_id Nullable(UUID),
    product_id Nullable(UUID),
    quantity Nullable(Int32),
    user_id Nullable(UUID),
    duration_ms Nullable(UInt32), -- Duration taken to complete tasks
    status String,              -- 'SUCCESS', 'FAILURE', 'CONGESTED'
    metadata Map(String, String) -- Flexible key-value pairs (e.g. YOLO confidence, error messages)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (warehouse_id, event_type, timestamp)
TTL timestamp + INTERVAL 2 YEAR;

-- 2. Environmental & IoT Sensor Telemetry Table
CREATE TABLE IF NOT EXISTS sensor_telemetry (
    timestamp DateTime64(3),
    sensor_id String,
    sensor_type String,        -- 'TEMPERATURE', 'HUMIDITY', 'SPEED', 'TRAFFIC_DENSITY'
    warehouse_id UUID,
    zone_id UUID,
    value Float64,
    metadata Map(String, String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (warehouse_id, zone_id, sensor_type, timestamp)
TTL timestamp + INTERVAL 2 YEAR;

-- 3. Warehouse/Zone Utilization Snapshots (For capacity trends)
CREATE TABLE IF NOT EXISTS utilization_snapshots (
    timestamp DateTime,
    warehouse_id UUID,
    zone_id UUID,
    total_bins UInt32,
    occupied_bins UInt32,
    utilization_rate Float64,
    total_volume_m3 Float64,
    used_volume_m3 Float64
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (warehouse_id, zone_id, timestamp)
TTL timestamp + INTERVAL 5 YEAR;

-- 4. AI Recommendation Performance & Audit Table
CREATE TABLE IF NOT EXISTS ai_recommendation_events (
    recommendation_id UUID,
    timestamp DateTime64(3),
    product_id UUID,
    requested_quantity UInt32,
    model_version String,       -- e.g. 'xgb-slotting-v1.0'
    recommended_bin_id UUID,
    confidence_score Float64,   -- confidence level [0.0 - 1.0]
    reasoning String,           -- model reasoning text
    is_accepted UInt8,          -- Boolean (0 or 1) indicating if operator placed it in recommended bin
    override_bin_id Nullable(UUID), -- The bin operator chose if they rejected the recommendation
    response_time_ms UInt32,    -- Inference latency in ms
    metadata Map(String, String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (product_id, model_version, timestamp)
TTL timestamp + INTERVAL 2 YEAR;

-- 5. SKU-Level Daily Velocity & Aggregated Analytics (For Slotting Optimization)
CREATE TABLE IF NOT EXISTS sku_velocity_analytics (
    date Date,
    product_id UUID,
    sku String,
    category_name String,
    total_picks UInt32,
    total_picked_quantity UInt32,
    total_putaways UInt32,
    total_putaway_quantity UInt32,
    inventory_turnover_rate Float64,
    velocity_class String       -- 'FAST', 'MEDIUM', 'SLOW'
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (product_id, date)
TTL date + INTERVAL 3 YEAR;
