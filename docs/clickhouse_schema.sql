-- ============================================================
--  NEW CLICKHOUSE ANALYTICS SCHEMA (7 TABLES)
-- ============================================================

-- 1. inventory_events (Tracks all warehouse activities/movements)
CREATE TABLE IF NOT EXISTS inventory_events
(
    event_id UUID,
    event_time DateTime,
    event_type String,
    product_id String,
    sku String,
    product_name String,
    quantity Int32,
    warehouse_id String,
    zone_code String,
    rack_code String,
    shelf_code String,
    bin_code String,
    source_location String,
    destination_location String,
    movement_type String,
    user_id String,
    ai_generated UInt8,
    confidence_score Float32
)
ENGINE = MergeTree()
ORDER BY (event_time, product_id);

-- 2. scan_events (For RFID/barcode scans)
CREATE TABLE IF NOT EXISTS scan_events
(
    scan_id UUID,
    scan_time DateTime,
    scan_type String,
    product_id String,
    sku String,
    zone_code String,
    rack_code String,
    shelf_code String,
    bin_code String,
    device_id String,
    worker_id String,
    scan_status String
)
ENGINE = MergeTree()
ORDER BY (scan_time, product_id);

-- 3. ai_predictions (Stores ML outputs)
CREATE TABLE IF NOT EXISTS ai_predictions
(
    prediction_id UUID,
    prediction_time DateTime,
    model_name String,
    prediction_type String,
    product_id String,
    recommended_zone String,
    recommended_bin String,
    utilization_score Float32,
    travel_distance Float32,
    confidence_score Float32,
    prediction_data String
)
ENGINE = MergeTree()
ORDER BY (prediction_time, product_id);

-- 4. warehouse_heatmaps (For activity analytics)
CREATE TABLE IF NOT EXISTS warehouse_heatmaps
(
    heatmap_time DateTime,
    zone_code String,
    aisle_code String,
    activity_count UInt32,
    avg_pick_time Float32,
    congestion_score Float32
)
ENGINE = MergeTree()
ORDER BY (heatmap_time, zone_code);

-- 5. route_analytics (Forklift/AGV analytics)
CREATE TABLE IF NOT EXISTS route_analytics
(
    route_id UUID,
    route_time DateTime,
    vehicle_type String,
    source_zone String,
    destination_zone String,
    distance_meters Float32,
    travel_time_seconds Float32,
    congestion_level Float32,
    optimized UInt8
)
ENGINE = MergeTree()
ORDER BY (route_time);

-- 6. sensor_events (IoT/Sensor analytics)
CREATE TABLE IF NOT EXISTS sensor_events
(
    sensor_id String,
    event_time DateTime,
    sensor_type String,
    zone_code String,
    temperature Float32,
    humidity Float32,
    vibration Float32,
    status String
)
ENGINE = MergeTree()
ORDER BY (event_time, sensor_id);

-- 7. demand_forecasts (Prediction analytics)
CREATE TABLE IF NOT EXISTS demand_forecasts
(
    forecast_time DateTime,
    product_id String,
    predicted_demand UInt32,
    forecast_window_days UInt32,
    confidence_score Float32
)
ENGINE = MergeTree()
ORDER BY (forecast_time, product_id);

-- ============================================================
--  OPERATIONAL ANALYTICS TABLES (4 TABLES)
-- ============================================================

-- 8. warehouse_events (Generic operational event log for all warehouse activities)
CREATE TABLE IF NOT EXISTS warehouse_events
(
    event_id UUID,
    event_type String,
    warehouse_id String,
    entity_type String,
    entity_id String,
    timestamp DateTime,
    metadata_json String
)
ENGINE = MergeTree()
ORDER BY (timestamp, warehouse_id, event_type);

-- 9. recommendation_metrics (Recommendation scoring and acceptance tracking)
CREATE TABLE IF NOT EXISTS recommendation_metrics
(
    recommendation_id String,
    warehouse_id String,
    score Float32,
    accepted UInt8,
    travel_distance Float32,
    timestamp DateTime
)
ENGINE = MergeTree()
ORDER BY (timestamp, warehouse_id);

-- 10. occupancy_metrics (Zone/rack occupancy percentages over time)
CREATE TABLE IF NOT EXISTS occupancy_metrics
(
    warehouse_id String,
    zone_id String,
    rack_id String,
    occupancy_percentage Float32,
    timestamp DateTime
)
ENGINE = MergeTree()
ORDER BY (timestamp, warehouse_id, zone_id);

-- 11. route_metrics (Route distance, nodes visited, and optimization scores)
CREATE TABLE IF NOT EXISTS route_metrics
(
    route_id String,
    warehouse_id String,
    distance Float32,
    nodes_visited UInt32,
    optimization_score Float32,
    timestamp DateTime
)
ENGINE = MergeTree()
ORDER BY (timestamp, warehouse_id);
