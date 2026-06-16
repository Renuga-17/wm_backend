# Backend-Frontend API Contract Verification Report

This report presents a comprehensive repository analysis of the API mappings in **wm_frontend** (`C:\TYN\wm_frontend`) verified against the actual API endpoints in the Django backend **wm_backend** (`C:\TYN\wm_backend`).

> [!NOTE]
> No source code in the backend or frontend repositories was modified during this analysis. A helper search utility was executed strictly in the local sandboxed scratch directory to identify frontend usages.

---

## 1. Key Architectural Mismatches

1. **Prefix Mismatch**:
   - The frontend uses `/warehouse/...`, `/manager/...`, `/staff/...`, and `/auth/...` prefixes, pointing to a mock WireMock API (`https://0jejz.wiremockapi.cloud`).
   - The backend defines all resources under the `/api/...` namespace (e.g., `/api/products/`, `/api/inventory/`, `/api/orders/`).

2. **Action / Resource Naming Differences**:
   - **OCR Subsystem**: The frontend defines endpoints such as `/ocr/process` and `/ocr/{docId}/verify`. The actual backend implements `/api/ocr/upload/` and `/api/ocr/documents/{id}/approve/`.
   - **Pluralization**: The frontend requests `/warehouse/order`, whereas the backend registers `/api/orders/` (plural).

3. **Stubs / Unwired Code**:
   - Many services in the frontend (e.g., `authService.js`, `inventoryService.js`, `productService.js`) are placeholders containing `TODO` comments.
   - The pages themselves use a local mock state (e.g., `AuthContext.jsx` for logins, `WarehouseContext.jsx` local state variables) instead of hitting these services.

---

## 2. API Mappings Summary Table

| Frontend Mapped Endpoint | HTTP Method | Frontend Service / Caller | Backend Path / Matcher | Status |
| :--- | :--- | :--- | :--- | :--- |
| `POST /auth/login` | POST | `authService.js` | `/api/users/login/` | **MISSING IN BACKEND** (Path mismatch) |
| `POST /auth/logout` | POST | `authService.js` | *None* | **MISSING IN BACKEND** |
| `POST /warehouse/inventory/adjust` | POST | `inventoryService.js` | *None* | **MISSING IN BACKEND** |
| `POST /warehouse/inventory/damage` | POST | `inventoryService.js` | *None* | **MISSING IN BACKEND** |
| `GET /manager/dashboard` | GET | `managerService.js` | *None* | **MISSING IN BACKEND** |
| `GET /manager/inbound/pending-assignments` | GET | `managerService.js` | *None* | **MISSING IN BACKEND** |
| `POST /manager/inbound/{inboundId}/recommend` | POST | `managerService.js` | *None* | **MISSING IN BACKEND** |
| `GET /manager/recommendations` | GET | `managerService.js` | *None* | **MISSING IN BACKEND** |
| `PUT /manager/recommendations/{id}/approve` | PUT | `managerService.js` | *None* | **MISSING IN BACKEND** |
| `PUT /manager/recommendations/{id}/reject` | PUT | `managerService.js` | *None* | **MISSING IN BACKEND** |
| `POST /manager/inbound/{inboundId}/regenerate` | POST | `managerService.js` | *None* | **MISSING IN BACKEND** |
| `POST /manager/tasks/assign` | POST | `managerService.js` | *None* | **MISSING IN BACKEND** |
| `GET /manager/tasks/staff` | GET | `managerService.js` | *None* | **MISSING IN BACKEND** |
| `GET /manager/layout` | GET | `managerService.js` | *None* | **MISSING IN BACKEND** |
| `POST /manager/layout/zones` | POST | `managerService.js` | `/api/zones/` | **MISSING IN BACKEND** (Path mismatch) |
| `PUT /manager/layout/zones/{id}` | PUT | `managerService.js` | `/api/zones/{id}/` | **MISSING IN BACKEND** (Path mismatch) |
| `POST /manager/layout/racks` | POST | `managerService.js` | `/api/warehouses/racks/` | **MISSING IN BACKEND** (Path mismatch) |
| `PUT /manager/layout/racks/{id}` | PUT | `managerService.js` | `/api/warehouses/racks/{id}/` | **MISSING IN BACKEND** (Path mismatch) |
| `POST /manager/layout/shelves` | POST | `managerService.js` | *None* | **MISSING IN BACKEND** |
| `PUT /manager/layout/shelves/{id}` | PUT | `managerService.js` | *None* | **MISSING IN BACKEND** |
| `POST /manager/layout/bins` | POST | `managerService.js` | `/api/bins/` | **MISSING IN BACKEND** (Path mismatch) |
| `PUT /manager/layout/bins/{id}` | PUT | `managerService.js` | `/api/bins/{id}/` | **MISSING IN BACKEND** (Path mismatch) |
| `GET /manager/layout/bins/occupancy` | GET | `managerService.js` | `/api/twin/occupancy` | **MISSING IN BACKEND** (Path mismatch) |
| `GET /manager/twin-telemetry` | GET | `managerService.js` | `/api/twin/summary` | **MISSING IN BACKEND** (Path mismatch) |
| `GET /manager/routes/task/{id}` | GET | `managerService.js` | *None* | **MISSING IN BACKEND** |
| `POST /ocr/process` | POST | `ocrService.js` | `/api/ocr/upload/` | **MISSING IN BACKEND** (Path mismatch) |
| `POST /inbound/receipt` | POST | `ocrService.js` | `/api/inbound/` | **MISSING IN BACKEND** (Path mismatch) |
| `PUT /ocr/{id}/verify` | PUT | `ocrService.js` | `/api/ocr/documents/{id}/approve/` | **MISSING IN BACKEND** (Path mismatch) |
| `POST /ocr/{id}/reject` | POST | `ocrService.js` | `/api/ocr/documents/{id}/reject/` | **MISSING IN BACKEND** (Path mismatch) |
| `POST /warehouse/order` | POST | `orderService.js` | `/api/orders/` | **MISSING IN BACKEND** (Path mismatch) |
| `PUT /warehouse/order/{id}/dispatch` | PUT | `orderService.js` | *None* | **MISSING IN BACKEND** |
| `GET /warehouse/products` | GET | `productService.js` | `/api/products/` | **MISSING IN BACKEND** (Path mismatch) |
| `GET /warehouse/products/{sku}` | GET | `productService.js` | `/api/products/{id}/` (via ID) | **MISSING IN BACKEND** (Path mismatch) |
| `PUT /warehouse/ai-recommendations/{id}/accept` | PUT | `recommendationService.js` | *None* | **MISSING IN BACKEND** |
| `PUT /warehouse/ai-recommendations/{id}/reject` | PUT | `recommendationService.js` | *None* | **MISSING IN BACKEND** |
| `GET /staff/putaway/assigned` | GET | `staffService.js` | *None* | **MISSING IN BACKEND** |
| `GET /staff/putaway/tasks/{id}` | GET | `staffService.js` | *None* | **MISSING IN BACKEND** |
| `POST /staff/putaway/tasks/{id}/start` | POST | `staffService.js` | *None* | **MISSING IN BACKEND** |
| `POST /staff/putaway/tasks/{id}/picked` | POST | `staffService.js` | *None* | **MISSING IN BACKEND** |
| `GET /staff/putaway/tasks/{id}/route` | GET | `staffService.js` | *None* | **MISSING IN BACKEND** |
| `POST /staff/putaway/tasks/{id}/reached` | POST | `staffService.js` | *None* | **MISSING IN BACKEND** |
| `POST /staff/putaway/tasks/{id}/complete` | POST | `staffService.js` | *None* | **MISSING IN BACKEND** |
| `POST /staff/putaway/tasks/{id}/issue` | POST | `staffService.js` | *None* | **MISSING IN BACKEND** |
| `GET /staff/movements` | GET | `staffService.js` | *None* | **MISSING IN BACKEND** |
| `GET /staff/putaway/completed` | GET | `staffService.js` | *None* | **MISSING IN BACKEND** |
| `POST /warehouse/zones` | POST | `warehouseService.js` | `/api/zones/` | **MISSING IN BACKEND** (Path mismatch) |
| `POST /warehouse/bins` | POST | `warehouseService.js` | `/api/bins/` | **MISSING IN BACKEND** (Path mismatch) |
| `GET /warehouse/warehouse-layout` | GET | `WarehouseContext.jsx` | `/api/layout/{layout_id}` | **MISSING IN BACKEND** (Path mismatch) |
| `GET /warehouse/utilization` | GET | `WarehouseContext.jsx` | `/api/twin/occupancy` | **MISSING IN BACKEND** (Path mismatch) |
| `GET /warehouse/inventory` | GET | `WarehouseContext.jsx` | `/api/inventory/` | **MISSING IN BACKEND** (Path mismatch) |
| `GET /warehouse/workers` | GET | `WarehouseContext.jsx` | `/api/users/` | **MISSING IN BACKEND** (Path mismatch) |
| `GET /warehouse/routes` | GET | `WarehouseContext.jsx` | `/api/routes/` | **MISSING IN BACKEND** (Path mismatch) |
| `GET /warehouse/order` | GET | `WarehouseContext.jsx` | `/api/orders/` | **MISSING IN BACKEND** (Path mismatch) |
| `GET /warehouse/movements` | GET | `WarehouseContext.jsx` | `/api/movements/` | **MISSING IN BACKEND** (Path mismatch) |
| `GET /warehouse/scanner-response` | GET | `WarehouseContext.jsx` | `/api/audit-logs/scan-logs/` | **MISSING IN BACKEND** (Path mismatch) |
| `GET /warehouse/suppliers` | GET | `WarehouseContext.jsx` | *None* | **MISSING IN BACKEND** |
| `GET /warehouse/products` | GET | `WarehouseContext.jsx` | `/api/products/` | **MISSING IN BACKEND** (Path mismatch) |
| `GET /warehouse/ai-recommendations` | GET | `WarehouseContext.jsx` | `/api/ai/recommendations/` | **MISSING IN BACKEND** (Path mismatch) |
| `GET /warehouse/inbound-shipments` | GET | `WarehouseContext.jsx` | `/api/inbound/` | **MISSING IN BACKEND** (Path mismatch) |

---

## 3. Detailed Verification Breakdown

### 3.1. Authentication Service (`authService.js`)

#### loginApi
- **Frontend Endpoint**: `POST /auth/login`
- **HTTP Method**: `POST`
- **Request Schema**: `{"email": "...", "password": "..."}`
- **Response Schema**: `{"token": "..."}`
- **Authentication Required**: No (Anonymous)
- **Frontend Page Using It**: `Login.jsx` (Currently defined but unused, page relies on local mock auth context).
- **Backend Status**: **MISSING IN BACKEND**
  - *Note*: The backend expects `POST /api/users/login/` (via JWT simple-jwt `TokenObtainPairView`), which requires `username` and `password` and returns `{"access": "...", "refresh": "..."}`.

#### logoutApi
- **Frontend Endpoint**: `POST /auth/logout`
- **HTTP Method**: `POST`
- **Request Schema**: None
- **Response Schema**: `{"success": true}`
- **Authentication Required**: Yes
- **Frontend Page Using It**: `Login.jsx` (Defined but unused).
- **Backend Status**: **MISSING IN BACKEND** (No endpoint exists for logout on the backend).

---

### 3.2. Inventory Service (`inventoryService.js`)

#### adjustStockApi
- **Frontend Endpoint**: `POST /warehouse/inventory/adjust`
- **HTTP Method**: `POST`
- **Request Schema**: `{"sku": "...", "qtyDelta": 10, "reason": "..."}`
- **Response Schema**: `{"success": true}`
- **Authentication Required**: Yes
- **Frontend Page Using It**: `clerk/StockAdjustment.jsx` (Defined but unused).
- **Backend Status**: **MISSING IN BACKEND** (No `/adjust` endpoint exists on `InventoryViewSet`).

#### reportDamageApi
- **Frontend Endpoint**: `POST /warehouse/inventory/damage`
- **HTTP Method**: `POST`
- **Request Schema**: `{"sku": "...", "qty": 10, "reason": "..."}`
- **Response Schema**: `{"success": true}`
- **Authentication Required**: Yes
- **Frontend Page Using It**: `clerk/DamagedStock.jsx` (Defined but unused).
- **Backend Status**: **MISSING IN BACKEND** (No `/damage` endpoint exists on `InventoryViewSet`).

---

### 3.3. Manager Service (`managerService.js`)

#### generateBinRecommendation
- **Frontend Endpoint**: `POST /manager/inbound/{inboundId}/recommend`
- **HTTP Method**: `POST`
- **Request Schema**: None
- **Response Schema**: `{"recommended_bin": "...", "confidence": ...}`
- **Authentication Required**: Yes
- **Frontend Page Using It**: `context/WarehouseContext.jsx`, `pages/AiRecommendations.jsx`, `pages/Dashboard.jsx`
- **Backend Status**: **MISSING IN BACKEND**
  - *Note*: The actual backend endpoint for storage recommendations is `POST /api/recommendations/suggest-bin/`, expecting `{"product_id": "...", "quantity": ..., "inbound_id": "..."}`.

#### assignPutawayTask
- **Frontend Endpoint**: `POST /manager/tasks/assign`
- **HTTP Method**: `POST`
- **Request Schema**: `{"inbound_id": "...", "staff_id": "..."}`
- **Response Schema**: `{"success": true}`
- **Authentication Required**: Yes
- **Frontend Page Using It**: `context/WarehouseContext.jsx`, `pages/AiRecommendations.jsx`, `pages/Dashboard.jsx`
- **Backend Status**: **MISSING IN BACKEND**

#### getBinOccupancy
- **Frontend Endpoint**: `GET /manager/layout/bins/occupancy`
- **HTTP Method**: `GET`
- **Request Schema**: None
- **Response Schema**: List of occupancy details
- **Authentication Required**: Yes
- **Frontend Page Using It**: `ZonesBins.jsx` (Defined but unused).
- **Backend Status**: **MISSING IN BACKEND**
  - *Note*: The actual backend endpoint is `GET /api/twin/occupancy`.

#### getDigitalTwinData
- **Frontend Endpoint**: `GET /manager/twin-telemetry`
- **HTTP Method**: `GET`
- **Request Schema**: None
- **Response Schema**: Telemetry JSON
- **Authentication Required**: Yes
- **Frontend Page Using It**: `DigitalTwin.jsx` (Defined but unused).
- **Backend Status**: **MISSING IN BACKEND**
  - *Note*: The actual backend endpoints are `GET /api/twin/summary` and `GET /api/twin/layout/{layout_id}`.

*(All other `managerService.js` endpoints are also marked as **MISSING IN BACKEND** due to prefix or route naming differences).*

---

### 3.4. OCR Document Service (`ocrService.js`)

#### verifyOcrDocument
- **Frontend Endpoint**: `PUT /ocr/{docId}/verify`
- **HTTP Method**: `PUT`
- **Request Schema**: `{"extractedItems": [...]}`
- **Response Schema**: `{"success": true}`
- **Authentication Required**: Yes
- **Frontend Page Using It**: `context/WarehouseContext.jsx`, `pages/OcrVerification.jsx`
- **Backend Status**: **MISSING IN BACKEND** (Route path mismatch).
  - *Actual Backend Matcher*: `POST /api/ocr/documents/{id}/approve/` (action `approve`)
    - **HTTP Method**: `POST`
    - **Request Schema**: `{"extracted_json": {...}}`
    - **Response Schema**: `{"success": true, "message": "...", "document_id": "...", "processing_status": "...", "shipment_code": "..."}`
    - **Authentication Required**: Yes

#### rejectOcrDocument
- **Frontend Endpoint**: `POST /ocr/{docId}/reject`
- **HTTP Method**: `POST`
- **Request Schema**: `{"reason": "string"}`
- **Response Schema**: `{"success": true}`
- **Authentication Required**: Yes
- **Frontend Page Using It**: `context/WarehouseContext.jsx`, `pages/OcrVerification.jsx`
- **Backend Status**: **MISSING IN BACKEND** (Route path mismatch).
  - *Actual Backend Matcher*: `POST /api/ocr/documents/{id}/reject/`
    - **HTTP Method**: `POST`
    - **Request Schema**: `{"reason": "string"}`
    - **Response Schema**: `{"success": true, "message": "...", "document_id": "...", "processing_status": "..."}`
    - **Authentication Required**: Yes

#### processOcrDocument
- **Frontend Endpoint**: `POST /ocr/process`
- **HTTP Method**: `POST`
- **Request Schema**: Multipart Form (`file`)
- **Response Schema**: Extracted fields JSON
- **Authentication Required**: Yes
- **Frontend Page Using It**: `OcrUpload.jsx` (Defined but unused).
- **Backend Status**: **MISSING IN BACKEND** (Route path mismatch).
  - *Actual Backend Matcher*: `POST /api/ocr/upload/`
    - **HTTP Method**: `POST`
    - **Request Schema**: Multipart Form (`file`, optional `document_type`)
    - **Response Schema**: `{"document_id": "uuid", "status": "uploaded"}`
    - **Authentication Required**: Yes

---

### 3.5. Staff Service (`staffService.js`)

#### startPutawayTask
- **Frontend Endpoint**: `POST /staff/putaway/tasks/{taskId}/start`
- **HTTP Method**: `POST`
- **Request Schema**: None
- **Response Schema**: `{"success": true}`
- **Authentication Required**: Yes
- **Frontend Page Using It**: `context/WarehouseContext.jsx`, `pages/staff/ActiveTask.jsx`, `pages/staff/PutawayTasks.jsx`, `pages/staff/StaffDashboard.jsx`
- **Backend Status**: **MISSING IN BACKEND**

#### confirmPickedFromReceiving
- **Frontend Endpoint**: `POST /staff/putaway/tasks/{taskId}/picked`
- **HTTP Method**: `POST`
- **Request Schema**: None
- **Response Schema**: `{"success": true}`
- **Authentication Required**: Yes
- **Frontend Page Using It**: `context/WarehouseContext.jsx`, `pages/staff/ActiveTask.jsx`, `pages/staff/StaffDashboard.jsx`
- **Backend Status**: **MISSING IN BACKEND**

#### confirmReachedBin
- **Frontend Endpoint**: `POST /staff/putaway/tasks/{taskId}/reached`
- **HTTP Method**: `POST`
- **Request Schema**: None
- **Response Schema**: `{"success": true}`
- **Authentication Required**: Yes
- **Frontend Page Using It**: `context/WarehouseContext.jsx`, `pages/staff/ActiveTask.jsx`, `pages/staff/StaffDashboard.jsx`
- **Backend Status**: **MISSING IN BACKEND**

#### completePutawayTask
- **Frontend Endpoint**: `POST /staff/putaway/tasks/{taskId}/complete`
- **HTTP Method**: `POST`
- **Request Schema**: `{"binId": "..."}`
- **Response Schema**: `{"success": true}`
- **Authentication Required**: Yes
- **Frontend Page Using It**: `context/WarehouseContext.jsx`, `pages/staff/ActiveTask.jsx`, `pages/staff/StaffDashboard.jsx`
- **Backend Status**: **MISSING IN BACKEND**

#### reportPutawayIssue
- **Frontend Endpoint**: `POST /staff/putaway/tasks/{taskId}/issue`
- **HTTP Method**: `POST`
- **Request Schema**: `{"issue": "..."}`
- **Response Schema**: `{"success": true}`
- **Authentication Required**: Yes
- **Frontend Page Using It**: `context/WarehouseContext.jsx`, `pages/staff/ActiveTask.jsx`
- **Backend Status**: **MISSING IN BACKEND**

*(All other `staffService.js` endpoints are also marked as **MISSING IN BACKEND**).*

---

### 3.6. Context Fetch Endpoints (`WarehouseContext.jsx`)

All direct fetches are executed inside `fetchData()` hook in `WarehouseContext.jsx` pointing to `${baseUrl}/warehouse/...`.

#### 1. GET `/warehouse/warehouse-layout`
- **Backend Endpoint Matcher**: `/api/layout/{layout_id}` or `/api/warehouses/`
- **Status**: **MISSING IN BACKEND** (Path mismatch)
  - *Backend Path*: `GET /api/layout/{layout_id}`
  - *HTTP Method*: `GET`
  - *Response Schema*: Layout details
  - *Authentication Required*: Yes

#### 2. GET `/warehouse/utilization`
- **Backend Endpoint Matcher**: `/api/twin/occupancy`
- **Status**: **MISSING IN BACKEND** (Path mismatch)
  - *Backend Path*: `GET /api/twin/occupancy`
  - *HTTP Method*: `GET`
  - *Response Schema*: Occupancy metrics
  - *Authentication Required*: Yes

#### 3. GET `/warehouse/inventory`
- **Backend Endpoint Matcher**: `/api/inventory/`
- **Status**: **MISSING IN BACKEND** (Path mismatch)
  - *Backend Path*: `GET /api/inventory/`
  - *HTTP Method*: `GET`
  - *Response Schema*: Array of Inventory objects
  - *Authentication Required*: Yes

#### 4. GET `/warehouse/workers`
- **Backend Endpoint Matcher**: `/api/users/`
- **Status**: **MISSING IN BACKEND** (Path mismatch)
  - *Backend Path*: `GET /api/users/`
  - *HTTP Method*: `GET`
  - *Response Schema*: Array of User objects
  - *Authentication Required*: Yes

#### 5. GET `/warehouse/routes`
- **Backend Endpoint Matcher**: `/api/routes/`
- **Status**: **MISSING IN BACKEND** (Path mismatch)
  - *Backend Path*: `GET /api/routes/`
  - *HTTP Method*: `GET`
  - *Response Schema*: Array of Route objects
  - *Authentication Required*: Yes

#### 6. GET `/warehouse/order`
- **Backend Endpoint Matcher**: `/api/orders/`
- **Status**: **MISSING IN BACKEND** (Path mismatch / Pluralization)
  - *Backend Path*: `GET /api/orders/`
  - *HTTP Method*: `GET`
  - *Response Schema*: Array of Order objects
  - *Authentication Required*: Yes

#### 7. GET `/warehouse/movements`
- **Backend Endpoint Matcher**: `/api/movements/`
- **Status**: **MISSING IN BACKEND** (Path mismatch)
  - *Backend Path*: `GET /api/movements/`
  - *HTTP Method*: `GET`
  - *Response Schema*: Array of Movement objects
  - *Authentication Required*: Yes

#### 8. GET `/warehouse/scanner-response`
- **Backend Endpoint Matcher**: `/api/audit-logs/scan-logs/`
- **Status**: **MISSING IN BACKEND** (Path mismatch)
  - *Backend Path*: `GET /api/audit-logs/scan-logs/`
  - *HTTP Method*: `GET`
  - *Response Schema*: Array of Scan log objects
  - *Authentication Required*: Yes

#### 9. GET `/warehouse/suppliers`
- **Backend Endpoint Matcher**: None
- **Status**: **MISSING IN BACKEND** (No supplier endpoints exist in backend).

#### 10. GET `/warehouse/products`
- **Backend Endpoint Matcher**: `/api/products/`
- **Status**: **MISSING IN BACKEND** (Path mismatch)
  - *Backend Path*: `GET /api/products/`
  - *HTTP Method*: `GET`
  - *Response Schema*: Array of Product objects
  - *Authentication Required*: Yes

#### 11. GET `/warehouse/ai-recommendations`
- **Backend Endpoint Matcher**: `/api/ai/recommendations/` or `/api/recommendations/`
- **Status**: **MISSING IN BACKEND** (Path mismatch)
  - *Backend Path*: `GET /api/ai/recommendations/`
  - *HTTP Method*: `GET`
  - *Response Schema*: Array of Recommendation objects
  - *Authentication Required*: Yes

#### 12. GET `/warehouse/inbound-shipments`
- **Backend Endpoint Matcher**: `/api/inbound/`
- **Status**: **MISSING IN BACKEND** (Path mismatch)
  - *Backend Path*: `GET /api/inbound/`
  - *HTTP Method*: `GET`
  - *Response Schema*: Array of Inbound shipment objects
  - *Authentication Required*: Yes
