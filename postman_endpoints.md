# Postman API Collection Endpoints

Here is a comprehensive list of all the API endpoints available in the Warehouse Management System backend. You can use these to create your Postman collection and test the application.

> [!NOTE]
> For endpoints using `{id}` or `{pk}`, replace them with the actual UUID or integer ID of the resource you are trying to access.

## Identity & Authentication
* **POST** `/api/users/login/` - Obtain JWT Token Pair (Access & Refresh)
* **POST** `/api/users/token/refresh/` - Refresh JWT Token
* **GET** `/api/users/` - List all users
* **POST** `/api/users/` - Create a new user
* **GET** `/api/users/{id}/` - Retrieve a specific user
* **PUT / PATCH** `/api/users/{id}/` - Update a user
* **DELETE** `/api/users/{id}/` - Delete a user

## Audit Logs
* **GET** `/api/audit-logs/` - List all audit logs
* **GET** `/api/audit-logs/{id}/` - Retrieve a specific audit log
* **GET** `/api/audit-logs/scan-logs/` - List all scan logs
* **GET** `/api/audit-logs/scan-logs/{id}/` - Retrieve a specific scan log

## Warehouse Layout
* **POST** `/api/layout/upload` - Upload a layout file
* **POST** `/api/layout/analyze` - Analyze an uploaded layout
* **GET** `/api/layout/entities` - Get spatial entities
* **GET** `/api/layout/{layout_id}` - Retrieve a specific layout configuration
* **PUT** `/api/layout/{layout_id}` - Update a layout configuration
* **DELETE** `/api/layout/{layout_id}` - Delete a layout configuration

## Digital Twin
* **GET** `/api/twin/layout/{layout_id}` - Get the digital twin layout representation
* **GET** `/api/twin/racks` - Get twin racks details
* **GET** `/api/twin/zones` - Get twin zones
* **GET** `/api/twin/occupancy` - View twin occupancy
* **GET** `/api/twin/paths` - Retrieve twin navigation paths
* **GET** `/api/twin/summary` - Get digital twin summary metrics

## Warehouses & Infrastructure
* **GET** `/api/warehouses/` - List all warehouses
* **POST** `/api/warehouses/` - Create a warehouse
* **GET** `/api/warehouses/{id}/` - Retrieve a specific warehouse
* **PUT / PATCH** `/api/warehouses/{id}/` - Update a warehouse
* **DELETE** `/api/warehouses/{id}/` - Delete a warehouse
* **GET / POST** `/api/warehouses/racks/` - List/Create Racks
* **GET / PUT / PATCH / DELETE** `/api/warehouses/racks/{id}/` - Manage specific rack
* **GET / POST** `/api/warehouses/spatial-entities/` - List/Create Spatial Entities
* **GET / POST** `/api/warehouses/navigation-nodes/` - List/Create Navigation Nodes
* **GET / POST** `/api/warehouses/paths/` - List/Create Navigation Paths
* **GET / POST** `/api/warehouses/rack-coordinates/` - List/Create Rack Coordinates

## Zones
* **GET** `/api/zones/` - List all zones
* **POST** `/api/zones/` - Create a zone
* **GET / PUT / PATCH / DELETE** `/api/zones/{id}/` - Manage specific zone
* **GET / POST** `/api/zones/boundaries/` - List/Create Zone boundaries
* **GET / PUT / PATCH / DELETE** `/api/zones/boundaries/{id}/` - Manage specific zone boundary

## Bins
* **GET** `/api/bins/` - List all bins
* **POST** `/api/bins/` - Create a bin
* **GET / PUT / PATCH / DELETE** `/api/bins/{id}/` - Manage specific bin

## Routes
* **GET / POST** `/api/routes/` - List/Create Routes
* **GET / PUT / PATCH / DELETE** `/api/routes/{id}/` - Manage specific route
* **POST** `/api/routes/generate/` - Generate a new route
* **POST** `/api/routes/block-path/` - Block a specific path
* **GET** `/api/routes/congestion/` - Get route congestion metrics
* **POST** `/api/routes/multi-pick/` - Optimize for multi-pick routing
* **POST** `/api/routes/optimize/` - Optimize general routes
* **POST** `/api/routes/recalculate/` - Recalculate routes dynamically

## Products
* **GET** `/api/products/` - List products
* **POST** `/api/products/` - Create a product
* **GET / PUT / PATCH / DELETE** `/api/products/{id}/` - Manage specific product

## Inventory
* **GET** `/api/inventory/` - List all inventory items
* **POST** `/api/inventory/` - Create an inventory item
* **GET / PUT / PATCH / DELETE** `/api/inventory/{id}/` - Manage specific inventory item

## Movements
* **GET** `/api/movements/` - List all movements
* **POST** `/api/movements/` - Create a movement
* **GET / PUT / PATCH / DELETE** `/api/movements/{id}/` - Manage specific movement
* **GET / POST** `/api/movements/allocations/` - Manage movement allocations

## AI & Recommendations
* **GET / POST** `/api/recommendations/` - List/Create generic recommendations
* **GET / PUT / PATCH / DELETE** `/api/recommendations/{id}/` - Manage generic recommendation
* **POST** `/api/recommendations/allocate/` - Get allocation recommendations
* **POST** `/api/recommendations/suggest-bin/` - Get bin suggestions
* **GET** `/api/ai/alerts/` - Fetch AI-generated alerts
* **GET** `/api/ai/congestion-risk/` - Analyze congestion risk
* **POST** `/api/ai/feedback/` - Provide feedback to AI
* **GET** `/api/ai/hotspot-prevention/` - Analyze hotspot prevention
* **GET** `/api/ai/operational-scores/` - View operational scores
* **POST** `/api/ai/optimize-slotting/` - Optimize slotting using AI
* **GET** `/api/ai/predict-demand/` - Demand prediction metrics
* **GET** `/api/ai/recommendations/` - AI Recommendations
* **GET** `/api/ai/slotting-score/` - Slotting Score overview

## Dashboards & Analytics
* **GET / POST** `/api/dashboards/` - List/Create Dashboard config
* **GET / PUT / PATCH / DELETE** `/api/dashboards/{id}/` - Manage Dashboard config
* **GET** `/api/dashboards/analytics/heatmaps/` - Generate warehouse heatmaps
* **GET** `/api/dashboards/analytics/routes/` - Analytics on routes
* **GET** `/api/dashboards/analytics/telemetry/` - Telemetry analytics
* **GET** `/api/dashboards/analytics/throughput/` - Throughput analytics
* **GET / POST** `/api/dashboards/robot-tasks/` - View Robot tasks metrics
* **GET / POST** `/api/dashboards/route-optimizations/` - View Route Optimization analytics

## Orders
* **GET** `/api/orders/` - List orders
* **POST** `/api/orders/` - Create an order
* **GET / PUT / PATCH / DELETE** `/api/orders/{id}/` - Manage specific order

## Inbound
* **GET** `/api/inbound/` - List inbound shipments
* **POST** `/api/inbound/` - Create an inbound shipment
* **GET / PUT / PATCH / DELETE** `/api/inbound/{id}/` - Manage inbound shipment

## OCR
* **POST** `/api/ocr/extract/` - Extract text via OCR (e.g., from shipping labels)
* **GET / POST** `/api/ocr/history/` - View OCR processing history
