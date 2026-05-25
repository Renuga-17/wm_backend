-- ============================================================
--  NEW NEON POSTGRESQL SCHEMA (26 TABLES)
-- ============================================================

-- 1. warehouses
CREATE TABLE warehouses (
    warehouse_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    location TEXT,
    total_area_sqft NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. warehouse_layouts
CREATE TABLE warehouse_layouts (
    layout_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(warehouse_id),
    layout_name VARCHAR(100),
    cad_file_url TEXT,
    width NUMERIC,
    height NUMERIC,
    depth NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. zones
CREATE TABLE zones (
    zone_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(warehouse_id),
    zone_name VARCHAR(100),
    zone_type VARCHAR(50),
    x NUMERIC,
    y NUMERIC,
    z NUMERIC,
    width NUMERIC,
    height NUMERIC,
    depth NUMERIC
);

-- 4. racks
CREATE TABLE racks (
    rack_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_id UUID REFERENCES zones(zone_id),
    rack_code VARCHAR(50) UNIQUE,
    max_weight NUMERIC,
    x NUMERIC,
    y NUMERIC,
    z NUMERIC,
    width NUMERIC,
    height NUMERIC,
    depth NUMERIC,
    rotation_angle NUMERIC
);

-- 5. shelves
CREATE TABLE shelves (
    shelf_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rack_id UUID REFERENCES racks(rack_id),
    shelf_number INT,
    max_weight NUMERIC,
    height_from_ground NUMERIC
);

-- 6. bins
CREATE TABLE bins (
    bin_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shelf_id UUID REFERENCES shelves(shelf_id),
    bin_code VARCHAR(50) UNIQUE,
    max_capacity NUMERIC,
    current_capacity NUMERIC DEFAULT 0,
    is_occupied BOOLEAN DEFAULT FALSE
);

-- 7. cad_objects
CREATE TABLE cad_objects (
    object_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layout_id UUID REFERENCES warehouse_layouts(layout_id),
    object_type VARCHAR(50),
    detected_label VARCHAR(100),
    confidence_score NUMERIC,
    x NUMERIC,
    y NUMERIC,
    z NUMERIC,
    width NUMERIC,
    height NUMERIC,
    depth NUMERIC
);

-- 8. ml_extractions
CREATE TABLE ml_extractions (
    extraction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    object_id UUID REFERENCES cad_objects(object_id),
    extracted_data JSONB,
    model_version VARCHAR(50),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. product_categories
CREATE TABLE product_categories (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_name VARCHAR(100) UNIQUE
);

-- 10. products
CREATE TABLE products (
    product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES product_categories(category_id),
    sku VARCHAR(100) UNIQUE,
    product_name VARCHAR(200),
    weight NUMERIC,
    is_fragile BOOLEAN DEFAULT FALSE,
    is_hazardous BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. product_dimensions
CREATE TABLE product_dimensions (
    dimension_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(product_id),
    length NUMERIC,
    width NUMERIC,
    height NUMERIC,
    box_length NUMERIC,
    box_width NUMERIC,
    box_height NUMERIC
);

-- 12. product_storage_rules
CREATE TABLE product_storage_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(product_id),
    allowed_zone_type VARCHAR(50),
    max_stack_height INT,
    required_temperature NUMERIC,
    orientation_rule VARCHAR(100)
);

-- 13. inventory
CREATE TABLE inventory (
    inventory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(product_id),
    total_quantity INT DEFAULT 0,
    reserved_quantity INT DEFAULT 0,
    damaged_quantity INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. inbound_shipments
CREATE TABLE inbound_shipments (
    inbound_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_code VARCHAR(100) UNIQUE,
    supplier_name VARCHAR(200),
    expected_arrival TIMESTAMP,
    status VARCHAR(50)
);

-- 15. outbound_shipments
CREATE TABLE outbound_shipments (
    outbound_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_code VARCHAR(100) UNIQUE,
    customer_name VARCHAR(200),
    dispatch_time TIMESTAMP,
    status VARCHAR(50)
);

-- 16. stock_movements
CREATE TABLE stock_movements (
    movement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(product_id),
    from_bin UUID REFERENCES bins(bin_id),
    to_bin UUID REFERENCES bins(bin_id),
    quantity INT,
    movement_type VARCHAR(50),
    moved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 17. storage_allocations
CREATE TABLE storage_allocations (
    allocation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(product_id),
    bin_id UUID REFERENCES bins(bin_id),
    quantity INT,
    allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 18. allocation_recommendations
CREATE TABLE allocation_recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(product_id),
    recommended_bin UUID REFERENCES bins(bin_id),
    confidence_score NUMERIC,
    reasoning JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 19. route_optimizations
CREATE TABLE route_optimizations (
    route_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_location VARCHAR(100),
    destination_location VARCHAR(100),
    optimized_path JSONB,
    estimated_time NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 20. warehouse_heatmaps
CREATE TABLE warehouse_heatmaps (
    heatmap_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_id UUID REFERENCES zones(zone_id),
    activity_score NUMERIC,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 21. ai_models
CREATE TABLE ai_models (
    model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100),
    model_version VARCHAR(50),
    accuracy NUMERIC,
    deployed_at TIMESTAMP
);

-- 22. ai_predictions
CREATE TABLE ai_predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES ai_models(model_id),
    prediction_type VARCHAR(100),
    prediction_result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 23. scan_logs
CREATE TABLE scan_logs (
    scan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(product_id),
    scan_type VARCHAR(50),
    scanned_location VARCHAR(100),
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 24. robot_tasks
CREATE TABLE robot_tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_type VARCHAR(100),
    source_location VARCHAR(100),
    destination_location VARCHAR(100),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 25. users
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(100),
    email VARCHAR(150) UNIQUE,
    role VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 26. audit_logs
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    action_type VARCHAR(100),
    table_name VARCHAR(100),
    record_id UUID,
    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 27. spatial_entities
CREATE TABLE spatial_entities (
    entity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(warehouse_id) ON DELETE CASCADE,
    entity_name VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    x NUMERIC NOT NULL,
    y NUMERIC NOT NULL,
    z NUMERIC NOT NULL,
    width NUMERIC NOT NULL,
    height NUMERIC NOT NULL,
    depth NUMERIC NOT NULL,
    rotation_angle NUMERIC DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 28. navigation_graph
CREATE TABLE navigation_graph (
    node_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(warehouse_id) ON DELETE CASCADE,
    node_name VARCHAR(100) NOT NULL,
    node_type VARCHAR(50) NOT NULL,
    x NUMERIC NOT NULL,
    y NUMERIC NOT NULL,
    z NUMERIC NOT NULL,
    connections JSONB DEFAULT '[]'
);

-- 29. warehouse_paths
CREATE TABLE warehouse_paths (
    path_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(warehouse_id) ON DELETE CASCADE,
    path_name VARCHAR(100) NOT NULL,
    start_x NUMERIC NOT NULL,
    start_y NUMERIC NOT NULL,
    start_z NUMERIC NOT NULL,
    end_x NUMERIC NOT NULL,
    end_y NUMERIC NOT NULL,
    end_z NUMERIC NOT NULL,
    width NUMERIC NOT NULL,
    is_two_way BOOLEAN DEFAULT TRUE
);

-- 30. zone_boundaries
CREATE TABLE zone_boundaries (
    boundary_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_id UUID REFERENCES zones(zone_id) ON DELETE CASCADE,
    polygon_points JSONB DEFAULT '[]'
);

-- 31. rack_coordinates
CREATE TABLE rack_coordinates (
    coordinate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rack_id UUID REFERENCES racks(rack_id) ON DELETE CASCADE,
    access_point_x NUMERIC NOT NULL,
    access_point_y NUMERIC NOT NULL,
    access_point_z NUMERIC NOT NULL,
    side VARCHAR(50) NOT NULL
);

