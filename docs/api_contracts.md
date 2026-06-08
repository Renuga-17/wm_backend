# API Contracts

This document outlines the API endpoints and contracts for the Warehouse Management System (WMS) + AI Storage Recommendation backend.

## Authentication
All API endpoints (except login/registration) require JWT authentication.
Headers:
```http
Authorization: Bearer <your_token>
```

## Endpoints

### Users
- `POST /api/users/` - List/Create users.
- `POST /api/users/login/` - Obtain JWT tokens.

### Warehouse Layout
- `GET /api/warehouses/` - List all warehouses.
- `POST /api/warehouses/` - Create a warehouse.
- `GET /api/zones/` - List zones within a warehouse.
- `GET /api/racks/` - List racks within a zone.
- `GET /api/bins/` - List bins within a rack.

### AI Recommendations
- `POST /api/recommendations/suggest-bin/` - Get AI placement recommendation for an incoming product.
  - **Request Body**:
    ```json
    {
      "product_id": "prod-102",
      "quantity": 50,
      "inbound_id": "inb-401"
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "recommended_bin_id": "bin-782",
      "confidence_score": 0.94,
      "reasoning": "Product has high turnover velocity; placing close to the dispatch zone (Zone A)."
    }
    ```

### Products
- `GET /api/products/` - List products.
- `POST /api/products/` - Create product.
- `GET /api/products/{id}/` - Retrieve product.
- `PUT /api/products/{id}/` - Update product.
- `PATCH /api/products/{id}/` - Partially update product.
- `DELETE /api/products/{id}/` - Delete product.

### Routes & Navigation
- Route Generation API
- Pathfinding API
- Navigation APIs

### Digital Twin
- `GET /api/twin/layout/{layout_id}/` - Get Layout Data
- `GET /api/twin/racks` - List racks in layout
- `GET /api/twin/zones` - List zones
- `GET /api/twin/occupancy` - Get space occupancy

### Analytics
- `GET /api/dashboards/analytics/heatmaps/` - Spatial Heatmaps
- `GET /api/dashboards/analytics/routes/` - Route Efficiency
- `GET /api/dashboards/analytics/telemetry/` - Sensor Telemetry
- `GET /api/dashboards/analytics/throughput/` - Inventory Throughput
*(Note: Analytics endpoints require `warehouse_id` query parameter)*

---
**Verification Status**: Phase 1 APIs (Users, Authentication, Warehouses, Zones, Products, Routes, Recommendations, Bins, Inventory, Orders, Digital Twin, Analytics) have been fully verified.
