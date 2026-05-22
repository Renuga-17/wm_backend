-- ============================================================
--  8,000 SQ FT WAREHOUSE – FULL NEON POSTGRESQL SCHEMA
--  Covers: Core WMS + Receiving + Dispatch + AI Recommendations
--  Compatible with: Neon (PostgreSQL 16)
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- SECTION 1: WAREHOUSE PHYSICAL STRUCTURE
-- ============================================================

-- 1. Warehouse
CREATE TABLE warehouses (
    warehouse_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    warehouse_code      VARCHAR(30)  UNIQUE NOT NULL,
    warehouse_name      VARCHAR(100) NOT NULL,
    total_area_sqft     NUMERIC(10,2) NOT NULL,          -- 8000
    length_ft           NUMERIC(10,2) NOT NULL,           -- 100
    width_ft            NUMERIC(10,2) NOT NULL,           -- 80
    clear_height_ft     NUMERIC(10,2),                    -- 28
    location            TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Dock Doors (Truck Entry / Receiving Exit)
--    Blueprint: Truck Entry 12×14 ft, Receiving Exit 12×14 ft
CREATE TABLE dock_doors (
    dock_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    warehouse_id        UUID NOT NULL REFERENCES warehouses(warehouse_id) ON DELETE CASCADE,
    dock_code           VARCHAR(20) UNIQUE NOT NULL,
    dock_name           VARCHAR(100),
    dock_type           VARCHAR(30) NOT NULL,             -- INBOUND / OUTBOUND / BOTH
    length_ft           NUMERIC(10,2),                    -- 12
    width_ft            NUMERIC(10,2),                    -- 14
    x_position_ft       NUMERIC(10,2),
    y_position_ft       NUMERIC(10,2),
    status              VARCHAR(30) DEFAULT 'AVAILABLE',  -- AVAILABLE / OCCUPIED / MAINTENANCE
    description         TEXT
);

-- 3. Warehouse Operational Areas
--    (Receiving, Scanning & Verification, Temp Racks, Packing, Admin, Utility etc.)
CREATE TABLE warehouse_areas (
    area_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    warehouse_id        UUID NOT NULL REFERENCES warehouses(warehouse_id) ON DELETE CASCADE,
    area_code           VARCHAR(30) UNIQUE NOT NULL,
    area_name           VARCHAR(100) NOT NULL,
    area_type           VARCHAR(50) NOT NULL,             -- RECEIVING / SCANNING / TEMP_RACKS / PACKING / ADMIN / UTILITY / SORTATION
    length_ft           NUMERIC(10,2),
    width_ft            NUMERIC(10,2),
    area_sqft           NUMERIC(10,2),
    x_position_ft       NUMERIC(10,2),
    y_position_ft       NUMERIC(10,2),
    description         TEXT
);

-- 4. Zone Groups (A=Fast, B=Medium, C=Heavy/Pallet, D=Small Parts)
CREATE TABLE zone_groups (
    zone_group_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    warehouse_id        UUID NOT NULL REFERENCES warehouses(warehouse_id) ON DELETE CASCADE,
    zone_group_code     VARCHAR(20) UNIQUE NOT NULL,      -- ZG-A / ZG-B / ZG-C / ZG-D
    zone_group_name     VARCHAR(100) NOT NULL,
    movement_type       VARCHAR(30),                      -- FAST / MEDIUM / HEAVY / SMALL_PARTS
    storage_purpose     VARCHAR(100),
    length_ft           NUMERIC(10,2),
    width_ft            NUMERIC(10,2),
    area_sqft           NUMERIC(10,2),
    x_position_ft       NUMERIC(10,2),
    y_position_ft       NUMERIC(10,2),
    priority_level      INT,
    max_volume_cuft     NUMERIC(12,2),
    current_volume_cuft NUMERIC(12,2) DEFAULT 0,
    utilization_percent NUMERIC(5,2)  DEFAULT 0,
    description         TEXT
);

-- 5. Internal Zones (A1–A4, B1–B3, C1–C4, D1–D4 = 15 total)
CREATE TABLE zones (
    zone_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zone_group_id       UUID NOT NULL REFERENCES zone_groups(zone_group_id) ON DELETE CASCADE,
    zone_code           VARCHAR(20) UNIQUE NOT NULL,      -- A1 / B2 / C3 etc.
    zone_name           VARCHAR(100),
    sequence_no         INT NOT NULL,                     -- ordering within group
    next_zone_id        UUID NULL REFERENCES zones(zone_id),  -- overflow chain: A1→A2→A3→A4
    length_ft           NUMERIC(10,2),
    width_ft            NUMERIC(10,2),
    area_sqft           NUMERIC(10,2),
    x_position_ft       NUMERIC(10,2),
    y_position_ft       NUMERIC(10,2),
    max_volume_cuft     NUMERIC(12,2),
    current_volume_cuft NUMERIC(12,2) DEFAULT 0,
    utilization_percent NUMERIC(5,2)  DEFAULT 0,
    status              VARCHAR(30) DEFAULT 'AVAILABLE'   -- AVAILABLE / FULL / MAINTENANCE
);

-- 6. Aisles
--    Blueprint: Main Forklift/AGV 12 ft, Zone A/B internal 10 ft,
--               Zone C (Heavy) 12 ft, Zone D (Small Parts) 8–10 ft,
--               Worker Safety 4 ft, Emergency 4 ft, Cross Aisles A & C
CREATE TABLE aisles (
    aisle_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    warehouse_id        UUID NOT NULL REFERENCES warehouses(warehouse_id) ON DELETE CASCADE,
    aisle_code          VARCHAR(30) UNIQUE NOT NULL,
    aisle_name          VARCHAR(100),
    aisle_type          VARCHAR(50),                      -- MAIN / INTERNAL / CROSS / SAFETY / EMERGENCY / AGV
    orientation         VARCHAR(20),                      -- HORIZONTAL / VERTICAL
    is_cross_aisle      BOOLEAN DEFAULT FALSE,            -- TRUE for Cross Aisle A & C
    length_ft           NUMERIC(10,2),
    width_ft            NUMERIC(10,2),                    -- 4 / 8 / 10 / 12 ft per blueprint
    x_position_ft       NUMERIC(10,2),
    y_position_ft       NUMERIC(10,2),
    allowed_vehicle     VARCHAR(50)                       -- FORKLIFT / AGV / MANUAL / NONE
);

-- 7. Aisle ↔ Zone Junction (replaces connected_zone_codes TEXT)
CREATE TABLE aisle_zones (
    aisle_id            UUID NOT NULL REFERENCES aisles(aisle_id) ON DELETE CASCADE,
    zone_id             UUID NOT NULL REFERENCES zones(zone_id) ON DELETE CASCADE,
    side                VARCHAR(10),                      -- LEFT / RIGHT (which side of aisle)
    PRIMARY KEY (aisle_id, zone_id)
);

-- ============================================================
-- SECTION 2: STORAGE UNITS
-- ============================================================

-- 8. Racks
--    Blueprint: Standard Rack (ZG-A/B, 8 ft H, 4 levels)
--               Heavy Duty Pallet Rack (ZG-C, 12 ft H, 3 levels, 6 pallets/rack)
--               Small Parts Rack (ZG-D, 7 ft H, 5 levels)
CREATE TABLE racks (
    rack_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zone_id             UUID NOT NULL REFERENCES zones(zone_id) ON DELETE CASCADE,
    rack_code           VARCHAR(30) UNIQUE NOT NULL,      -- ZG-A / A1 / R02 per location code
    rack_type           VARCHAR(50),                      -- STANDARD / PALLET / SMALL_PARTS
    length_ft           NUMERIC(10,2),
    depth_ft            NUMERIC(10,2),
    height_ft           NUMERIC(10,2),
    x_position_ft       NUMERIC(10,2),
    y_position_ft       NUMERIC(10,2),
    total_levels        INT,                              -- 4 / 3 / 5 per rack type
    pallets_per_level   INT,                              -- Zone C: 2 pallets/level (6 total / 3 levels)
    max_load_kg         NUMERIC(10,2),                    -- 1000–1200 kg / 4800–6000 kg / 800–1000 kg
    current_load_kg     NUMERIC(10,2) DEFAULT 0,
    max_volume_cuft     NUMERIC(12,2),
    current_volume_cuft NUMERIC(12,2) DEFAULT 0,
    utilization_percent NUMERIC(5,2)  DEFAULT 0,
    status              VARCHAR(30) DEFAULT 'ACTIVE'      -- ACTIVE / INACTIVE / MAINTENANCE
);

-- 9. Shelves
CREATE TABLE shelves (
    shelf_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rack_id             UUID NOT NULL REFERENCES racks(rack_id) ON DELETE CASCADE,
    shelf_code          VARCHAR(30) UNIQUE NOT NULL,      -- .../ L03 in location code
    level_no            INT NOT NULL,                     -- 1 = ground level
    height_from_floor_ft NUMERIC(10,2),
    shelf_length_ft     NUMERIC(10,2),
    shelf_depth_ft      NUMERIC(10,2),
    shelf_height_ft     NUMERIC(10,2),                   -- shelf gap (2 ft standard, 1.3 ft small parts)
    max_load_kg         NUMERIC(10,2),                    -- 100–150 kg / 800–1000 kg / 100–150 kg
    current_load_kg     NUMERIC(10,2) DEFAULT 0,
    max_volume_cuft     NUMERIC(12,2),
    current_volume_cuft NUMERIC(12,2) DEFAULT 0,
    utilization_percent NUMERIC(5,2)  DEFAULT 0,
    status              VARCHAR(30) DEFAULT 'ACTIVE'
);

-- 10. Bins
--     Blueprint: Standard Bin (L:2ft W:1.5ft H:1.5ft, 20–30 kg)
--                Medium Bin   (L:1.5ft W:1ft H:1ft, 40–60 kg)
--                Pallet Pos   (L:4ft W:3.3ft H:3.3ft, 500–750 kg)
CREATE TABLE bins (
    bin_id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shelf_id            UUID NOT NULL REFERENCES shelves(shelf_id) ON DELETE CASCADE,
    bin_code            VARCHAR(40) UNIQUE NOT NULL,      -- full location: ZG-A/A1/R02/L03/B04
    bin_type            VARCHAR(50),                      -- STANDARD / MEDIUM / PALLET
    length_ft           NUMERIC(10,2),
    width_ft            NUMERIC(10,2),
    height_ft           NUMERIC(10,2),
    max_volume_cuft     NUMERIC(12,2),
    current_volume_cuft NUMERIC(12,2) DEFAULT 0,
    max_weight_kg       NUMERIC(10,2),
    current_weight_kg   NUMERIC(10,2) DEFAULT 0,
    utilization_percent NUMERIC(5,2)  DEFAULT 0,
    status              VARCHAR(30) DEFAULT 'EMPTY'       -- EMPTY / PARTIAL / FULL / RESERVED
);

-- ============================================================
-- SECTION 3: PRODUCTS & CATEGORIES
-- ============================================================

-- 11. Product Categories
--     Blueprint top 5: Wireless Mouse, Mobile Charger Adapter,
--     Earbuds/TWS, Fasteners/Hardware Kit, Barcode Scanner Accessories
CREATE TABLE product_categories (
    category_id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_code               VARCHAR(30) UNIQUE NOT NULL,
    category_name               VARCHAR(100) NOT NULL,
    preferred_zone_group_code   VARCHAR(20),              -- ZG-A / ZG-B / ZG-C / ZG-D
    preferred_storage_type      VARCHAR(50),              -- BIN / SHELF / RACK / PALLET
    movement_type               VARCHAR(30),              -- FAST / MEDIUM / SLOW
    description                 TEXT
);

-- 12. Products / SKUs
CREATE TABLE products (
    product_id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id                 UUID REFERENCES product_categories(category_id),
    sku                         VARCHAR(50) UNIQUE NOT NULL,
    product_name                VARCHAR(100) NOT NULL,
    brand                       VARCHAR(100),
    model                       VARCHAR(100),
    -- Physical dimensions (product itself)
    product_length_in           NUMERIC(10,2),
    product_width_in            NUMERIC(10,2),
    product_height_in           NUMERIC(10,2),
    -- Box/packaging dimensions
    box_length_in               NUMERIC(10,2),
    box_width_in                NUMERIC(10,2),
    box_height_in               NUMERIC(10,2),
    box_volume_cuin             NUMERIC(12,2),
    weight_kg                   NUMERIC(10,2),
    -- Storage attributes
    storage_type                VARCHAR(50),              -- BIN / SHELF / RACK / PALLET
    recommended_zone_group_code VARCHAR(20),
    velocity_type               VARCHAR(30),              -- FAST / MEDIUM / SLOW
    abc_class                   VARCHAR(5),               -- A / B / C
    fragile                     BOOLEAN DEFAULT FALSE,
    stackable                   BOOLEAN DEFAULT TRUE,
    created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SECTION 4: INBOUND (RECEIVING) WORKFLOW
-- ============================================================

-- 13. Inbound Shipments / Purchase Orders
CREATE TABLE inbound_shipments (
    shipment_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    warehouse_id        UUID NOT NULL REFERENCES warehouses(warehouse_id),
    dock_id             UUID REFERENCES dock_doors(dock_id),
    shipment_ref        VARCHAR(50) UNIQUE NOT NULL,      -- PO / ASN reference
    supplier_name       VARCHAR(100),
    vehicle_no          VARCHAR(30),
    expected_date       DATE,
    arrived_at          TIMESTAMP,
    status              VARCHAR(30) DEFAULT 'EXPECTED',   -- EXPECTED / ARRIVED / UNLOADING / QC / PUTAWAY / COMPLETED
    total_skus          INT DEFAULT 0,
    total_qty           INT DEFAULT 0,
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. Goods Receipt Note (GRN) Line Items
--     Blueprint: Receiving area steps → Unloading, Inspection, Counting, Quality Check
CREATE TABLE grn_items (
    grn_item_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shipment_id         UUID NOT NULL REFERENCES inbound_shipments(shipment_id) ON DELETE CASCADE,
    product_id          UUID NOT NULL REFERENCES products(product_id),
    expected_qty        INT NOT NULL DEFAULT 0,
    received_qty        INT NOT NULL DEFAULT 0,
    rejected_qty        INT DEFAULT 0,
    batch_no            VARCHAR(50),
    expiry_date         DATE,
    qc_status           VARCHAR(30) DEFAULT 'PENDING',    -- PENDING / PASSED / FAILED / PARTIAL
    qc_notes            TEXT,
    received_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SECTION 5: INVENTORY
-- ============================================================

-- 15. Inventory (current stock positions)
CREATE TABLE inventory (
    inventory_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id          UUID NOT NULL REFERENCES products(product_id),
    warehouse_id        UUID NOT NULL REFERENCES warehouses(warehouse_id),
    zone_id             UUID REFERENCES zones(zone_id),
    rack_id             UUID REFERENCES racks(rack_id),
    shelf_id            UUID REFERENCES shelves(shelf_id),
    bin_id              UUID REFERENCES bins(bin_id),
    quantity            INT NOT NULL DEFAULT 0,
    reserved_quantity   INT DEFAULT 0,
    available_quantity  INT GENERATED ALWAYS AS (quantity - reserved_quantity) STORED,
    batch_no            VARCHAR(50),
    last_updated        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 16. Inventory Movements (full audit trail)
--     Includes rack & shelf FKs for granular shelf-level transfer tracking
CREATE TABLE inventory_movements (
    movement_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id          UUID NOT NULL REFERENCES products(product_id),
    shipment_id         UUID REFERENCES inbound_shipments(shipment_id),   -- linked for INBOUND
    order_id            UUID,                                              -- FK to outbound_orders (added below)
    -- From location
    from_zone_id        UUID REFERENCES zones(zone_id),
    from_rack_id        UUID REFERENCES racks(rack_id),
    from_shelf_id       UUID REFERENCES shelves(shelf_id),
    from_bin_id         UUID REFERENCES bins(bin_id),
    -- To location
    to_zone_id          UUID REFERENCES zones(zone_id),
    to_rack_id          UUID REFERENCES racks(rack_id),
    to_shelf_id         UUID REFERENCES shelves(shelf_id),
    to_bin_id           UUID REFERENCES bins(bin_id),
    -- Movement details
    movement_type       VARCHAR(50),                      -- INBOUND / PUTAWAY / PICK / TRANSFER / DISPATCH / RETURN
    quantity            INT NOT NULL,
    reason              TEXT,
    moved_by            VARCHAR(100),
    moved_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SECTION 6: OUTBOUND (DISPATCH) WORKFLOW
-- ============================================================

-- 17. Outbound Orders
--     Blueprint: Packing & Dispatch, 3 Packing Stations, Sortation Conveyor,
--                Dispatch Staging, Label Printing
CREATE TABLE outbound_orders (
    order_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    warehouse_id        UUID NOT NULL REFERENCES warehouses(warehouse_id),
    dock_id             UUID REFERENCES dock_doors(dock_id),
    order_ref           VARCHAR(50) UNIQUE NOT NULL,
    customer_name       VARCHAR(100),
    channel             VARCHAR(50),                      -- B2B / D2C / MARKETPLACE etc.
    priority            VARCHAR(20) DEFAULT 'NORMAL',     -- URGENT / HIGH / NORMAL / LOW
    requested_date      DATE,
    status              VARCHAR(30) DEFAULT 'NEW',        -- NEW / PICKING / PACKING / STAGED / DISPATCHED / CANCELLED
    packing_station_no  INT,                              -- 1 / 2 / 3 (3 stations in blueprint)
    vehicle_no          VARCHAR(30),
    dispatched_at       TIMESTAMP,
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 18. Pick Lists (line items per outbound order)
CREATE TABLE pick_list_items (
    pick_item_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id            UUID NOT NULL REFERENCES outbound_orders(order_id) ON DELETE CASCADE,
    product_id          UUID NOT NULL REFERENCES products(product_id),
    -- Suggested pick location (from AI or WMS)
    zone_id             UUID REFERENCES zones(zone_id),
    rack_id             UUID REFERENCES racks(rack_id),
    shelf_id            UUID REFERENCES shelves(shelf_id),
    bin_id              UUID REFERENCES bins(bin_id),
    requested_qty       INT NOT NULL DEFAULT 0,
    picked_qty          INT DEFAULT 0,
    status              VARCHAR(30) DEFAULT 'PENDING',    -- PENDING / PICKED / SHORT / CANCELLED
    picked_by           VARCHAR(100),
    picked_at           TIMESTAMP
);

-- Add FK from inventory_movements back to outbound_orders
ALTER TABLE inventory_movements
    ADD CONSTRAINT fk_movement_order
    FOREIGN KEY (order_id) REFERENCES outbound_orders(order_id);

-- ============================================================
-- SECTION 7: AI STORAGE RECOMMENDATIONS
-- ============================================================

-- 19. AI Storage Recommendations
--     Supports putaway suggestions, overflow logic, confidence scoring
CREATE TABLE ai_storage_recommendations (
    recommendation_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id              UUID NOT NULL REFERENCES products(product_id),
    -- Recommended location
    recommended_zone_id     UUID REFERENCES zones(zone_id),
    recommended_rack_id     UUID REFERENCES racks(rack_id),
    recommended_shelf_id    UUID REFERENCES shelves(shelf_id),
    recommended_bin_id      UUID REFERENCES bins(bin_id),
    -- Recommendation context
    recommendation_reason   TEXT,
    confidence_score        NUMERIC(5,2),                 -- 0.00–100.00
    overflow_applied        BOOLEAN DEFAULT FALSE,        -- TRUE when primary zone was FULL
    source_zone_id          UUID REFERENCES zones(zone_id), -- original zone before overflow
    -- Lifecycle
    status                  VARCHAR(30) DEFAULT 'PENDING', -- PENDING / APPLIED / REJECTED / EXPIRED
    applied_by              VARCHAR(100),
    applied_at              TIMESTAMP,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SECTION 8: USEFUL INDEXES FOR NEON PERFORMANCE
-- ============================================================

-- Inventory lookups by location
CREATE INDEX idx_inventory_bin         ON inventory(bin_id);
CREATE INDEX idx_inventory_zone        ON inventory(zone_id);
CREATE INDEX idx_inventory_product     ON inventory(product_id);
CREATE INDEX idx_inventory_warehouse   ON inventory(warehouse_id);

-- Movement audit trail
CREATE INDEX idx_movements_product     ON inventory_movements(product_id);
CREATE INDEX idx_movements_type        ON inventory_movements(movement_type);
CREATE INDEX idx_movements_order       ON inventory_movements(order_id);
CREATE INDEX idx_movements_shipment    ON inventory_movements(shipment_id);
CREATE INDEX idx_movements_moved_at    ON inventory_movements(moved_at);

-- Pick list lookups
CREATE INDEX idx_pick_order            ON pick_list_items(order_id);
CREATE INDEX idx_pick_product          ON pick_list_items(product_id);
CREATE INDEX idx_pick_status           ON pick_list_items(status);

-- Zone overflow chain
CREATE INDEX idx_zones_next            ON zones(next_zone_id);
CREATE INDEX idx_zones_group           ON zones(zone_group_id);
CREATE INDEX idx_zones_status          ON zones(status);

-- AI recommendations
CREATE INDEX idx_ai_product            ON ai_storage_recommendations(product_id);
CREATE INDEX idx_ai_status             ON ai_storage_recommendations(status);

-- Bins availability
CREATE INDEX idx_bins_status           ON bins(status);
CREATE INDEX idx_bins_shelf            ON bins(shelf_id);

-- Racks per zone
CREATE INDEX idx_racks_zone            ON racks(zone_id);

-- Aisle-zone junction
CREATE INDEX idx_aisle_zones_zone      ON aisle_zones(zone_id);
CREATE INDEX idx_aisle_zones_aisle     ON aisle_zones(aisle_id);

-- Shipments
CREATE INDEX idx_shipments_status      ON inbound_shipments(status);
CREATE INDEX idx_shipments_dock        ON inbound_shipments(dock_id);

-- Orders
CREATE INDEX idx_orders_status         ON outbound_orders(status);
CREATE INDEX idx_orders_dock           ON outbound_orders(dock_id);
