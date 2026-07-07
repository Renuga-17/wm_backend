# Warehouse Management + AI Storage Recommendation (wm_backend)

This is the backend repository for the **Warehouse Management System (WMS) with AI Storage Recommendation**. Built on **Django** and **Django REST Framework**, the backend coordinates inventory activities, schedules item movements, records comprehensive analytics, and interfaces with multiple specialized databases.

---

## 🏗️ Architecture & Tech Stack

- **Core Framework**: Django & DRF
- **Primary DB**: PostgreSQL (relational data)
- **Cache & Locks**: Redis
- **Document DB**: MongoDB
- **Analytics DB**: ClickHouse
- **Vector DB**: Qdrant
- **AI Recommendation Engine**: External FastAPI service

---

## 📁 Repository Structure

```
wm_backend/
├─ config/               # Django settings & URLs
├─ apps/                 # Domain modules
│   ├─ users/
│   ├─ warehouses/
│   ├─ zones/
│   ├─ racks/
│   ├─ bins/
│   ├─ products/
│   ├─ inventory/
│   ├─ inbound/
│   ├─ orders/
│   ├─ movements/
│   ├─ recommendations/
│   ├─ dashboards/
│   └─ audit_logs/
├─ common/               # Shared utilities
├─ integrations/         # Connectors (MongoDB, Redis, ClickHouse, Qdrant, AI)
├─ docs/                 # Architecture diagrams
├─ scripts/               # Dev tools, seeding
└─ tests/                # Pytest suite
```

---

## 🛠️ Local Setup

1. **Prerequisites**: Python 3.10+, Docker (optional).
2. **Installation**:
   ```bash
   git clone <repo_url>
   cd wm_backend
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Environment**: Copy `.env.example` → `.env` and configure DB URIs.
4. **Migrations & Seeding**:
   ```bash
   python manage.py migrate
   python scripts/create_superuser.py
   python scripts/seed_data.py
   ```
5. **Run Server**:
   ```bash
   python manage.py runserver
   ```
   Server available at http://127.0.0.1:8000/

---

## 📈 Project Completion Status

- **Backend Foundation**: 100%
- **Warehouse Management**: 100%
- **API Verification**: 100%
- **OCR Integration**: 100%
- **Digital Twin**: 100%
- **Analytics**: 0% (next phase)
- **Recommendation Engine**: 0% (pending verification)
- **RAG**: 0% (pending)
- **YOLO/OpenCV**: 0% (pending)

**Overall Project Completion:** **60%**

---

## 🚀 Next Phase

**Phase 3B – Analytics Completion**
- Analytics verification
- Dashboard validation
- ClickHouse validation
- Throughput, heatmap, route, telemetry analytics

## 📚 Documentation Hub

For a comprehensive understanding of the system, please refer to the following documentation files:

- **[System Architecture](docs/system_architecture.md)**: High-level overview of how the Frontend, Backend, and RAG services interact.
- **[API Contracts](docs/api_contracts.md)**: Detailed JSON payloads and endpoint definitions.
- **[Postman Endpoints](postman_endpoints.md)**: List of Postman collections for local testing.
- **[Digital Twin Documentation](document.md)**: Detailed status and endpoints related to the 3D Digital Twin and OCR integration.
- **[Frontend System](../wm_frontend/README.md)**: Setup and architecture for the React interface.
- **[RAG Service](../wm_rag/README.md)**: Setup and architecture for the FastAPI AI assistant.

---

*Documentation updated to reflect latest project status.*
