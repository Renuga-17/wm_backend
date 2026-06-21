# Digital Twin Final Documentation

## Completed Phases

### Phase 1 – API Verification

Completed:

- Authentication APIs
- Users APIs
- Warehouses APIs
- Zones APIs
- Products APIs
- Bins APIs
- Inventory APIs
- Orders APIs
- Routes APIs
- Recommendations APIs
- Analytics APIs
- Digital Twin APIs

**Status:** 100% Complete

---

### Phase 2 – OCR Integration

Completed:

- OCR Microservice Integration
- OCRDocument Model
- OCR Service Client
- OCR APIs
- OCR Result Storage
- OCR Verification

**Endpoints:**

- `POST /api/ocr/extract/`
- `GET /api/ocr/history/`

**Status:** 100% Complete

---

### Phase 3A – Digital Twin

Completed:

- Layout API
- Racks API
- Zones API
- Occupancy API
- Paths API
- Summary API
- NetworkX Shortest Path Generation
- Digital Twin Verification

**Endpoints:**

- `GET /api/twin/layout/{id}/`
- `GET /api/twin/racks`
- `GET /api/twin/zones`
- `GET /api/twin/occupancy`
- `GET /api/twin/paths`
- `GET /api/twin/summary`

**Verification Results:**

- layout → 200
- racks → 200
- zones → 200
- occupancy → 200
- paths → 200
- summary → 200

**Status:** 100% Complete

---

## API Endpoints Reference

This section outlines the request and response structures for all API categories in the system.

### 1. Authentication & Users API
- **POST `/api/users/login/`**
  - **Description**: Authenticate user and retrieve JWT tokens.
  - **Request Body**:
    ```json
    {
      "username": "admin",
      "password": "password123"
    }
    ```
  - **Response (200 OK)**:
    ```json
    {
      "access": "eyJhbGci...",
      "refresh": "eyJhbGci..."
    }
    ```

- **POST `/api/users/token/refresh/`**
  - **Description**: Refresh access token using refresh token.
  - **Request Body**:
    ```json
    {
      "refresh": "eyJhbGci..."
    }
    ```
  - **Response (200 OK)**:
    ```json
    {
      "access": "eyJhbGci..."
    }
    ```

- **GET `/api/users/`**
  - **Description**: List all users.
  - **Response (200 OK)**:
    ```json
    [
      {
        "id": "2d9b626c-d2c6-43b8-89c0-f8fb235d9a91",
        "username": "user1",
        "email": "user1@example.com",
        "role": "STAFF",
        "warehouse": "f3b39d1b-0bf2-411a-85d7-ecf927e1f13b",
        "first_name": "John",
        "last_name": "Doe"
      }
    ]
    ```

- **POST `/api/users/`**
  - **Description**: Create a new user.
  - **Request Body**:
    ```json
    {
      "username": "newuser",
      "email": "new@example.com",
      "role": "MANAGER",
      "warehouse": "f3b39d1b-0bf2-411a-85d7-ecf927e1f13b",
      "first_name": "Jane",
      "last_name": "Smith"
    }
    ```
  - **Response (201 Created)**:
    ```json
    {
      "id": "c8b417df-32ef-4d37-9759-9941a54b38bf",
      "username": "newuser",
      "email": "new@example.com",
      "role": "MANAGER",
      "warehouse": "f3b39d1b-0bf2-411a-85d7-ecf927e1f13b",
      "first_name": "Jane",
      "last_name": "Smith"
    }
    ```

- **GET `/api/users/{id}/`**
  - **Description**: Retrieve detailed information of a specific user.
  - **Response (200 OK)**:
    ```json
    {
      "id": "2d9b626c-d2c6-43b8-89c0-f8fb235d9a91",
      "username": "user1",
      "email": "user1@example.com",
      "role": "STAFF",
      "warehouse": "f3b39d1b-0bf2-411a-85d7-ecf927e1f13b",
      "first_name": "John",
      "last_name": "Doe"
    }
    ```

- **PUT `/api/users/{id}/`** / **PATCH `/api/users/{id}/`**
  - **Description**: Fully or partially update user details.
  - **Request Body**: (Partial / full user fields)
  - **Response (200 OK)**: Updated user object.

- **DELETE `/api/users/{id}/`**
  - **Description**: Delete a specific user.
  - **Response (204 No Content)**: Empty body.

---

### 2. Warehouses & Layout API
- **POST `/api/layout/upload`**
  - **Description**: Upload a warehouse CAD layout file (DXF/DWG).
  - **Request Body (multipart/form-data)**:
    - `warehouse_id`: "f3b39d1b-0bf2-411a-85d7-ecf927e1f13b" (UUID)
    - `layout_name`: "Main Warehouse East Layout" (string)
    - `file`: (binary CAD file)
    - `width`: 150.00 (optional, decimal)
    - `height`: 100.00 (optional, decimal)
    - `depth`: 30.00 (optional, decimal)
  - **Response (201 Created)**:
    ```json
    {
      "id": "d0be1330-84cf-4ca6-a517-76b3f7f8976b",
      "warehouse": "f3b39d1b-0bf2-411a-85d7-ecf927e1f13b",
      "layout_name": "Main Warehouse East Layout",
      "cad_file_url": "/media/layouts/layout_file.dxf",
      "width": "150.00",
      "height": "100.00",
      "depth": "30.00",
      "created_at": "2026-06-10T17:15:00Z"
    }
    ```

- **POST `/api/layout/analyze`**
  - **Description**: Parse CAD layout using AI / Vision to automatically extract and register zones, racks, and obstacles.
  - **Request Body**:
    ```json
    {
      "layout_id": "d0be1330-84cf-4ca6-a517-76b3f7f8976b"
    }
    ```
  - **Response (200 OK)**:
    ```json
    {
      "success": true,
      "layout_id": "d0be1330-84cf-4ca6-a517-76b3f7f8976b",
      "entities_found": 15,
      "entities_created": 15,
      "extracted_objects": [
        {
          "id": "a9a83411-fa2c-47b2-bd74-4b53ef51d02d",
          "type": "rack",
          "name": "RACK-A1",
          "coordinates": [12.5, 45.3, 0.0]
        }
      ]
    }
    ```

- **GET `/api/layout/entities`**
  - **Description**: Retrieve detected CAD objects and ML extraction data.
  - **Query Parameters**: `layout_id` (required, UUID)
  - **Response (200 OK)**:
    ```json
    [
      {
        "object_id": "a9a83411-fa2c-47b2-bd74-4b53ef51d02d",
        "object_type": "rack",
        "detected_label": "RACK-A1",
        "confidence_score": 0.985,
        "dimensions": {
          "width": 10.0,
          "height": 2.5,
          "depth": 3.0
        },
        "coordinates": {
          "x": 12.5,
          "y": 45.3,
          "z": 0.0
        },
        "extracted_metadata": {
          "rotation": 0.0,
          "points": []
        }
      }
    ]
    ```

- **GET `/api/layout/{layout_id}`**
  - **Description**: Retrieve layout details.
  - **Response (200 OK)**: Warehouse layout record.

- **CRUD Endpoints for Warehouses & Spatial Entities (`/api/warehouses/`)**:
  - `GET /api/warehouses/` / `POST /api/warehouses/`: Manage warehouse sites.
  - `GET /api/warehouses/racks/`: List and manage physical racks.
  - `GET /api/warehouses/spatial-entities/`: Manage general spatial entities (e.g. obstacles, pathways, docks).
  - `GET /api/warehouses/navigation-nodes/`: Manage navigation graph nodes.
  - `GET /api/warehouses/paths/`: Manage pathways.
  - `GET /api/warehouses/rack-coordinates/`: Manage rack coordinate access points.

---

### 3. Digital Twin API
- **GET `/api/twin/layout/{layout_id}`**
  - **Description**: Retrieve a fully compiled digital twin payload for the layout including zones, racks, spatial entities, paths, and navigation nodes.
  - **Response (200 OK)**:
    ```json
    {
      "layout": { "id": "uuid", "layout_name": "..." },
      "zones": [
        {
          "id": "uuid",
          "zone_name": "Dry Storage",
          "boundaries": [{ "id": "uuid", "polygon_points": [] }]
        }
      ],
      "racks": [
        {
          "id": "uuid",
          "rack_code": "RACK-A1",
          "shelves": [
            {
              "id": "uuid",
              "shelf_number": 1,
              "bins": [{ "id": "uuid", "bin_code": "A1-01" }]
            }
          ]
        }
      ],
      "spatial_entities": [],
      "paths": [],
      "navigation_nodes": []
    }
    ```

- **GET `/api/twin/racks`**
  - **Description**: Retrieve all racks with nested shelves and bins.
  - **Response (200 OK)**: List of detailed racks.

- **GET `/api/twin/zones`**
  - **Description**: Retrieve all zones with boundary coordinates.
  - **Response (200 OK)**: List of detailed zones.

- **GET `/api/twin/occupancy`**
  - **Description**: Retrieve overall and per-rack bin occupancy details.
  - **Response (200 OK)**:
    ```json
    {
      "overall": {
        "total_bins": 500,
        "occupied_bins": 220,
        "occupancy_percentage": 44.0
      },
      "racks": [
        {
          "rack_id": "uuid",
          "rack_code": "RACK-A1",
          "total_bins": 20,
          "occupied_bins": 12,
          "occupancy_percentage": 60.0
        }
      ]
    }
    ```

- **GET `/api/twin/paths`**
  - **Description**: Get all paths and navigation nodes, falling back to Dijkstra's all-pairs shortest paths graph.
  - **Response (200 OK)**: Path and navigation node graph representation.

- **GET `/api/twin/summary`**
  - **Description**: Get top-level metrics of digital twin components.
  - **Response (200 OK)**:
    ```json
    {
      "total_warehouses": 1,
      "total_zones": 3,
      "total_racks": 12,
      "total_bins": 240,
      "occupancy_percentage": 45.83,
      "navigation_node_count": 35,
      "navigation_edge_count": 58
    }
    ```

---

### 4. Zones & Bins API
- **CRUD `/api/zones/`**
  - **Description**: List, retrieve, create, update, delete zones. Response includes dynamic predictive/cognitive AI attributes.
  - **Response (200 OK)**:
    ```json
    {
      "id": "uuid",
      "warehouse": "uuid",
      "zone_name": "Dry Storage",
      "zone_type": "DRY",
      "x": "0.00", "y": "0.00", "z": "0.00",
      "width": "50.00", "height": "50.00", "depth": "50.00",
      "congestion_risk": 0.15,
      "activity_score": 0.45,
      "predictive_occupancy": 0.60,
      "ai_slotting_scores": [
        {
          "bin_code": "BIN-A01",
          "product_sku": "SKU-99",
          "score": 92.4
        }
      ]
    }
    ```

- **CRUD `/api/zones/boundaries/`**
  - **Description**: Manage zone coordinate boundaries (polygons).
  - **Response (200 OK)**: Boundary vertices.

- **CRUD `/api/bins/`**
  - **Description**: Manage physical storage bins inside racks.
  - **Response (200 OK)**: Bin status and dimensions.

---

### 5. Products, Inventory & Inbound API
- **CRUD `/api/products/`**
  - **Description**: Register and manage SKU products.
  - **Fields**: `id`, `category` (category ID), `sku` (string), `product_name`, `weight` (decimal), `is_fragile` (bool), `is_hazardous` (bool), `created_at`.

- **CRUD `/api/inventory/`**
  - **Description**: Track product inventory volumes.
  - **Fields**: `id`, `product`, `total_quantity`, `reserved_quantity`, `damaged_quantity`, `updated_at`.

- **CRUD `/api/inbound/`**
  - **Description**: Manage expected supplier shipments.
  - **Fields**: `id`, `shipment_code`, `supplier_name`, `expected_arrival` (datetime), `status`.

---

### 6. Orders & Stock Movements API
- **CRUD `/api/orders/`**
  - **Description**: Manage outbound dispatch shipments.
  - **Fields**: `id`, `shipment_code`, `customer_name`, `dispatch_time` (datetime), `status`.

- **CRUD `/api/movements/`**
  - **Description**: Record actual stock transfers between bins.
  - **Fields**: `id`, `product`, `from_bin`, `to_bin`, `quantity`, `movement_type`, `moved_at`.

- **CRUD `/api/movements/allocations/`**
  - **Description**: Allocate inventory directly to bins.
  - **Fields**: `id`, `product`, `bin`, `quantity`, `allocated_at`.

---

### 7. Recommendations & AI Recommendations API
- **POST `/api/recommendations/suggest-bin/`**
  - **Description**: Suggest an optimal storage bin for a product based on AI predictions.
  - **Request Body**:
    ```json
    {
      "product_id": "SKU-12345",
      "quantity": 50,
      "inbound_id": "uuid (optional)"
    }
    ```
  - **Response (200 OK)**:
    ```json
    {
      "success": true,
      "recommended_bin_id": "d041e127-ec17-48f8-b39d-b8d2ec2c412f",
      "confidence_score": 0.95,
      "reasoning": "Optimal turnover allocation near dispatch dock."
    }
    ```

- **POST `/api/recommendations/allocate/`**
  - **Description**: Commit stock allocation using AI-recommended slotting logic.
  - **Request Body**:
    ```json
    {
      "product_id": "uuid",
      "quantity": 50
    }
    ```
  - **Response (201 Created)**: Allocations details indicating exact zone/rack/shelf/bin.

- **POST `/api/ai/predict-demand/`**
  - **Description**: Predict future demand volume score (0.0 to 1.0) for a product.
  - **Request Body**:
    ```json
    {
      "product_id": "uuid",
      "days_history": 30
    }
    ```
  - **Response (200 OK)**:
    ```json
    {
      "id": "uuid",
      "product": "uuid",
      "product_sku": "SKU-123",
      "product_name": "Wireless Mouse",
      "predicted_demand_score": "0.8200",
      "forecast_period": "DAILY",
      "confidence_score": "0.9100",
      "forecasted_at": "datetime"
    }
    ```

- **POST `/api/ai/optimize-slotting/`**
  - **Description**: Triggers optimization for slotting recommendations.
  - **Request Body**:
    ```json
    {
      "product_id": "uuid",
      "warehouse_id": "uuid"
    }
    ```
  - **Response (200 OK)**: Optimization recommendation payload.

- **GET `/api/ai/congestion-risk/`**
  - **Description**: Retrieve congestion predictions for all warehouse zones.
  - **Query Parameters**: `warehouse_id` (required, UUID)
  - **Response (200 OK)**: Predictive traffic volume and risk scores.

- **GET `/api/ai/slotting-score/`**
  - **Description**: Fetch detailed slotting analysis rewards and penalties score components.
  - **Query Parameters**: `product_id` (required), `warehouse_id` (required)
  - **Response (200 OK)**:
    ```json
    [
      {
        "bin_code": "BIN-A01",
        "zone_name": "Dry Storage",
        "score": 85.5,
        "proximity_reward": 10.0,
        "congestion_penalty": 0.0,
        "travel_cost": 5.5,
        "affinity_bonus": 2.0
      }
    ]
    ```

- **GET `/api/ai/hotspot-prevention/`** / **GET `/api/ai/operational-scores/`**
  - **Description**: Retrieve active hotspots and overall warehouse operational efficiency metrics.

- **GET/POST `/api/ai/alerts/`**
  - **Description**: Fetch active system warnings or mark alerts as resolved by posting `alert_id`.

- **POST `/api/ai/feedback/`**
  - **Description**: Feed back operational durations (e.g. pick times) into the reinforcement learning loop.
  - **Request Body**:
    ```json
    {
      "signal_type": "PICK_DURATION",
      "payload": {
        "duration": 45.5,
        "benchmark": 40.0,
        "decision_id": "uuid"
      }
    }
    ```
  - **Response (200 OK)**: Ingestion confirmation receipt.

---

### 8. Dashboards & ClickHouse Analytics API
- **CRUD `/api/dashboards/robot-tasks/`** / **CRUD `/api/dashboards/route-optimizations/`**
  - **Description**: Track active warehouse robotics tasks and route optimization histories.

- **GET `/api/dashboards/analytics/heatmaps/`**
  - **Description**: Get spatial coordinates heatmap representing forklift and picker activity.
  - **Query Parameters**: `warehouse_id` (required), `start_time`, `end_time` (optional)
  - **Response (200 OK)**: Analytical layout coordinates and hit frequencies.

- **GET `/api/dashboards/analytics/routes/`** / **telemetry/** / **throughput/**
  - **Description**: Retrieve route efficiency patterns, IoT telemetry data, and stock turnover volumes.
  - **Query Parameters**: `warehouse_id` (required), `start_time`, `end_time` (optional)

---

### 9. Audit & Scan Logs API
- **CRUD `/api/audit-logs/`**
  - **Description**: Audit database mutations (inserts, updates, deletes) per user.
  - **Fields**: `id`, `user`, `action_type`, `table_name`, `record_id`, `action_time`.

- **CRUD `/api/audit-logs/scan-logs/`**
  - **Description**: Audit scanner events on incoming/outgoing items.
  - **Fields**: `id`, `product`, `scan_type`, `scanned_location`, `scanned_at`.

---

### 10. Routes & Pathfinding API
- **POST `/api/routes/optimize/`**
  - **Description**: Find optimal single-destination path inside warehouse using A* pathfinding.
  - **Request Body**:
    ```json
    {
      "warehouse_id": "f3b39d1b-0bf2-411a-85d7-ecf927e1f13b",
      "start": "DOCK_A",
      "targets": ["RACK-B1"]
    }
    ```
  - **Response (201 Created)**:
    ```json
    {
      "id": "uuid",
      "start_location": "DOCK_A",
      "distance": "15.50",
      "estimated_time": 10,
      "path": [[10.5, 20.0], [12.0, 20.0], [15.0, 20.0]],
      "created_at": "datetime"
    }
    ```

- **POST `/api/routes/multi-pick/`**
  - **Description**: Compute multi-stop picking route solving Travelling Salesperson Problem (TSP) with Nearest Neighbor logic.
  - **Request Body**:
    ```json
    {
      "warehouse_id": "f3b39d1b-0bf2-411a-85d7-ecf927e1f13b",
      "start": "DOCK_A",
      "targets": ["RACK-B1", "RACK-C4", "DOCK_B"]
    }
    ```
  - **Response (201 Created)**: TSP path list of segments and distance.

- **GET `/api/routes/congestion/`**
  - **Description**: Retrieve all route navigation edges along with real-time costs and congestion details.
  - **Query Parameters**: `warehouse_id` (required)
  - **Response (200 OK)**: Directed graph edge list.

- **POST `/api/routes/block-path/`**
  - **Description**: Mark specific edges as blocked or highly congested (updates weights in route graph).
  - **Request Body**:
    ```json
    {
      "warehouse_id": "uuid",
      "from_node_id": "uuid",
      "to_node_id": "uuid",
      "is_blocked": true
    }
    ```
  - **Response (200 OK)**: Updated navigation edge.

- **POST `/api/routes/recalculate/`**
  - **Description**: Dynamic recalculation of a route to bypass newly blocked/congested nodes.
  - **Request Body**:
    ```json
    {
      "route_id": "uuid"
    }
    ```
  - **Response (200 OK)**: Recalculated route payload.

- **POST `/api/routes/generate/`**
  - **Description**: Map physical bins to navigation nodes and calculate shortest path between them.
  - **Request Body**:
    ```json
    {
      "source_bin_id": "uuid",
      "destination_bin_id": "uuid"
    }
    ```
  - **Response (200 OK)**:
    ```json
    {
      "success": true,
      "distance": 8.75,
      "path": [
        { "node_id": "uuid", "node_name": "A-01-Node", "x": 5.5, "y": 12.0, "z": 0.0 }
      ]
    }
    ```

---

### 11. OCR API
- **POST `/api/ocr/extract/`**
  - **Description**: Submit document URL for synchronous text extraction and automatic RAG database ingestion.
  - **Request Body**:
    ```json
    {
      "document_name": "Supplier Manifest Jan 2026",
      "document_type": "manifest",
      "document_url": "https://example.com/manifest-jan-2026.pdf"
    }
    ```
  - **Response (200 OK)**:
    ```json
    {
      "id": "uuid",
      "document_name": "Supplier Manifest Jan 2026",
      "document_type": "manifest",
      "document_url": "https://example.com/manifest-jan-2026.pdf",
      "extracted_text": "Extracted manifest items details...",
      "structured_data": null,
      "status": "COMPLETED",
      "error_message": null,
      "created_at": "datetime",
      "updated_at": "datetime"
    }
    ```

- **GET `/api/ocr/history/`** / **GET `/api/ocr/history/{id}/`**
  - **Description**: Browse past OCR extraction logs.

---

## Current Project Status

- **Backend Foundation:** 100%
- **Warehouse Management:** 100%
- **API Verification:** 100%
- **OCR Integration:** 100%
- **Digital Twin:** 100%
- **Analytics:** 0% (next phase)
- **Recommendation Engine:** 0% (pending verification)
- **RAG:** 0% (pending)
- **YOLO/OpenCV:** 0% (pending)

**Overall Project Completion:** 60%

---

## Next Phase

**Phase 3B – Analytics Completion**

Tasks:

- Analytics verification
- Dashboard validation
- ClickHouse validation
- Throughput analytics
- Heatmap analytics
- Route analytics
- Telemetry analytics

---

*Documentation updated to reflect latest project status.*
