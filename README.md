# Warehouse Management + AI Storage Recommendation (wm_backend)

This is the backend repository for the **Warehouse Management System (WMS) with AI Storage Recommendation** system. Built on **Django** and **Django REST Framework**, the backend coordinates inventory activities, schedules items movements, records comprehensive analytics, and interfaces with multiple specialized databases.

---

## 🏗️ Architecture & Tech Stack

Our backend is designed for high responsiveness, scaling telemetry ingestion, and vector embeddings lookup:

- **Core Framework**: Django & Django REST Framework (DRF)
- **Primary Database**: PostgreSQL (Neon DB) - Stores relational data (users, warehouse layout, active inventory status, orders).
- **In-Memory Cache & Lock Store**: Redis - Caches query results and manages concurrent inventory transaction locks.
- **Document Database**: MongoDB - Stores unstructured logs, carrier payloads, and dynamic shipping labels.
- **Column-Oriented Analytics DB**: ClickHouse - Houses high-volume event logs, telemetry (e.g. zone temperature), and warehouse traffic tracking.
- **Vector Database**: Qdrant - Stores semantic embeddings of product profiles for optimal shelf compatibility search.
- **AI Recommendation Engine**: Connected to a specialized external FastAPI AI service via HTTP API (`integrations/ai_service_client.py`).

---

## 📁 Repository Structure

```text
wm_backend/
│
├── config/                  # Django project configuration settings & URLs
├── apps/                    # Business domain modules
│   ├── users/               # Custom user identities, roles, and profiles
│   ├── warehouses/          # Warehouse physical structures
│   ├── zones/               # Sub-warehouse areas (dry, cold, hazardous)
│   ├── racks/               # Racks within zones
│   ├── bins/                # Individual slots/bins on racks
│   ├── products/            # SKUs, dimensions, and product properties
│   ├── inventory/           # Current physical inventory balances
│   ├── inbound/             # Receiving workflows and purchase orders
│   ├── orders/              # Picking list and sales order outbound fulfillment
│   ├── movements/           # Movement tickets from bin to bin (replenishment, putaway)
│   ├── recommendations/     # Placement suggestions integrating with AI
│   ├── dashboards/          # Operations metrics and real-time dashboard endpoints
│   └── audit_logs/          # Historical change logs of system state changes
│
├── common/                  # Shared exceptions, permissions, and response wrappers
├── integrations/            # Connectors for MongoDB, Redis, Clickhouse, Qdrant, AI Service
├── docs/                    # Architecture diagrams and specifications
├── scripts/                 # Dev tools, seeding, and initialization scripts
└── tests/                   # Pytest testing fixtures
```

---

## 🛠️ Local Setup Steps

### 1. Prerequisites
- **Python**: version 3.10 or higher
- **Docker** (Optional, recommended for running local instances of Redis, Clickhouse, Qdrant, MongoDB, and PostgreSQL)

### 2. Installation
Clone the repository and enter the directory:
```bash
git clone <repository_url> wm_backend
cd wm_backend
```

Create a virtual environment and activate it:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

### 3. Environment Settings
Create a `.env` file in the root directory by copying the example:
```bash
cp .env.example .env
```
Update the database connection URIs inside `.env` to point to your PostgreSQL, Redis, MongoDB, Clickhouse, and Qdrant instances.

### 4. Running Migrations & Seeding
```bash
# Run django migrations
python manage.py migrate

# Create local superuser
python scripts/create_superuser.py

# Seed mock database values (warehouses, zones, bins, products)
python scripts/seed_data.py
```

### 5. Running the Dev Server
To start Django's local server:
```bash
python manage.py run_server
```
The server will run on [http://127.0.0.1:8000/](http://127.0.0.1:8000/).
