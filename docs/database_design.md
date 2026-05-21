# Database Design

Our architecture uses a multi-database approach optimized for high performance, analytical scale, unstructured logs, and vector operations.

```mermaid
graph TD
    PostgreSQL[(PostgreSQL/Neon DB)] --> |Core Relations| RelationalData[Users, Warehouses, Bins, Products, Orders]
    Redis[(Redis)] --> |Caching & Locks| CacheData[Inventory Locks, Session tokens]
    MongoDB[(MongoDB)] --> |Unstructured JSON| DocumentData[Carrier API Payloads, External Event Logs]
    ClickHouse[(ClickHouse)] --> |Analytics & Metrics| TelemetryData[Audit Logs, Temperature logs, Movement Speed]
    Qdrant[(Qdrant Vector DB)] --> |Embeddings| VectorData[Product Dimensions, Semantic Compatibility]
```

## Relational Schema (PostgreSQL)

### 1. `users_user`
- `id` (UUID, PK)
- `username` (VARCHAR)
- `email` (VARCHAR)
- `role` (ENUM: ADMIN, MANAGER, STAFF)

### 2. `warehouses_warehouse`
- `id` (UUID, PK)
- `code` (VARCHAR, Unique)
- `name` (VARCHAR)
- `address` (TEXT)

### 3. `zones_zone`
- `id` (UUID, PK)
- `warehouse_id` (FK to warehouse)
- `code` (VARCHAR)
- `zone_type` (ENUM: DRY, COLD, HAZARDOUS)

### 4. `racks_rack`
- `id` (UUID, PK)
- `zone_id` (FK to zone)
- `code` (VARCHAR)

### 5. `bins_bin`
- `id` (UUID, PK)
- `rack_id` (FK to rack)
- `code` (VARCHAR)
- `max_weight` (DECIMAL)
- `max_volume` (DECIMAL)

### 6. `products_product`
- `id` (UUID, PK)
- `sku` (VARCHAR)
- `name` (VARCHAR)
- `dimensions` (JSON)
- `weight` (DECIMAL)
