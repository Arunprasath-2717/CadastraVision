# CadastraVision — AI-Powered Cadastral Intelligence Platform

CadastraVision is a full-stack land administration platform designed to streamline cadastral parcel management, topological validation, conflict resolution, tamper-evident audit logging, and geospatial exports.

> [!NOTE]
> **AI Runtime Isolation Notice**: This integration baseline intentionally excludes AI runtime dependencies (PyTorch, FastSAM, YOLOv8). The application operates deterministically using database-backed records and GeoJSON feature endpoints. AI model services will be integrated in a subsequent phase.

---

## 🏗️ Architecture

```
React / Vite / Mapbox GL Frontend
           │
           │ REST API + JWT Bearer Auth
           ▼
FastAPI Async Backend Core
           │
           │ Async SQLAlchemy 2.x ORM
           ▼
PostgreSQL / PostGIS Database
           │
 ┌─────────┴─────────┐
 ▼                   ▼
Audit Log         GeoJSON / CSV Exports
(SHA-256 Chain)
```

---

## 🌿 Authoritative Integration Sources

The system target branch `integration/full-system` is selectively integrated from:

| Layer | Source Remote Branch | Description |
|---|---|---|
| **Database Schema** | `origin/main` | PostGIS tables & Alembic migration baseline (`7a8e910f1112`) |
| **Backend Engine** | `origin/backend/siva-core` | FastAPI async routers, services, Pydantic schemas |
| **Audit/Security/Export**| `origin/feature/backend-audit-security-export` | RBAC, security headers, SHA-256 audit chaining, export pipeline |
| **Frontend UI** | `origin/frontend` | Authoritative React 18 + Vite + Mapbox GL PWA |

---

## ⚡ Quick Start Options

### Option A: Docker Compose (Recommended)

Start the full stack (PostgreSQL/PostGIS, FastAPI backend, Vite frontend) with a single command:

```bash
docker compose up --build
```

* **Frontend App**: [http://localhost:5173](http://localhost:5173)
* **Backend API Docs (Swagger)**: [http://localhost:8001/docs](http://localhost:8001/docs)
* **OpenAPI Schema**: [http://localhost:8001/openapi.json](http://localhost:8001/openapi.json)

---

### Option B: Local Development Setup

#### 1. Backend Server Setup

##### For Bash / Zsh Users:
```bash
cd backend
source .venv/bin/activate
.venv/bin/python -m alembic upgrade head
PYTHONPATH=. .venv/bin/python scripts/seed_demo.py
.venv/bin/python -m uvicorn app.main:app --reload --port 8001
```

##### For Fish Shell Users:
```fish
cd backend
source .venv/bin/activate.fish
.venv/bin/python -m alembic upgrade head
env PYTHONPATH=. .venv/bin/python scripts/seed_demo.py
.venv/bin/python -m uvicorn app.main:app --reload --port 8001
```

#### 2. Frontend Application Setup
```bash
cd frontend
npm install
npm run dev
```

The frontend will start at `http://localhost:5173` (or `http://localhost:5174` if 5173 is occupied).

---

## 🔐 Demo Credentials & RBAC Roles

The idempotent seed script (`scripts/seed_demo.py`) pre-configures three demo user accounts with server-enforced Role-Based Access Control (RBAC):

| Role | Email | Password | Permissions |
|---|---|---|---|
| **ADMIN** | `admin@cadastravision.gov` | `Admin123!` | Full system administration, approval overrides, audit log verification, export access |
| **ANALYST** | `surveyor@cadastravision.gov` | `Surveyor123!` | Parcel geometry editing, validation flag processing, conflict resolution |
| **VIEWER** | `viewer@cadastravision.gov` | `Viewer123!` | Read-only access to GIS maps, parcels, and audit data. (Mutations return HTTP 403 Forbidden) |

---

## 🧪 Testing & Verification Suite

Run the full automated verification suite across all system layers:

### 1. Full Master Verification Script
```bash
./scripts/master_backend_verify.sh
```

### 2. Backend Pytest Test Suite (280/280 Passed)
```bash
cd backend
.venv/bin/python -m pytest -q
```

### 3. Security Unit & Integration Tests (48/48 Passed)
```bash
cd backend
.venv/bin/python -m pytest tests/test_security.py -v
```

### 4. Production Frontend Build (1602 Modules Transformed)
```bash
cd frontend
npm run build
```

### 5. Full End-to-End (E2E) Smoke Test (8/8 Passed)
```bash
# Start backend server on port 8001
cd backend
.venv/bin/python -m uvicorn app.main:app --port 8001 &
SERVER_PID=$!
sleep 3

# Run live E2E smoke test
cd ..
backend/.venv/bin/python scripts/e2e_smoke_test.py

# Shutdown server
kill $SERVER_PID
```

---

## 🔐 Security & Audit Subsystem

* **Password Hashing**: `bcrypt` (12 rounds) with salt.
* **Token Handling**: Standard JWT Bearer tokens with signature validation and expiration enforcement.
* **Audit Trail**: Tamper-evident SHA-256 hash chaining on all parcel mutation events.
* **Security Headers**: Includes `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, and `X-Request-ID`.
* **Exports**: Authorized GeoJSON, CSV, and JSON parcel exports backed by database records.

---

## 🔧 Troubleshooting

### Port Conflicts
If port 8001 or 5173 is in use, terminate active processes:
```bash
fuser -k 8001/tcp 5173/tcp
```

### Virtual Environment Sourcing in Fish Shell
Do not run `source .venv/bin/activate` in Fish shell. Use:
```fish
source .venv/bin/activate.fish
```
or invoke python directly: `.venv/bin/python`.
