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
