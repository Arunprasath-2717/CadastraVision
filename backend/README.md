# CadastraVision Backend — Core Service (PRD-CM-03)

Production-ready **FastAPI** backend for the CadastralMap AI-enabled automated cadastral mapping platform (**SIH 2026, PS 26012**).

## Status: Phase 3 Complete (Core Workflows Implemented)

* **26/26 PRD Endpoints**: Registered under `/v1` namespace with database-backed services.
* **10/10 Domain Models**: SQLAlchemy 2.x async ORM models capturing the complete AI imagery & parcel pipeline.
* **Imagery & AI Pipeline Service (`ImageryService`)**: File ingestion, GeoTIFF validation, tile creation, and AI segmentation job dispatch hook (Akshaya).
* **Parcel Workflow & Topology Engine (`ParcelService`)**: Parcel CRUD, geometric edit processing, topology validation execution (Arun), and state machine lifecycle (`draft` -> `validation_pending` -> `validated` -> `approved` / `rejected`).
* **SHA-256 Audit Trail (`AuditEventService`)**: Cryptographic hash chaining (`prev_hash` & `entry_hash`) for tamper-evident audit logging (Prajith).
* **Offline Sync & Idempotency Engine**: Persistent batch action replay with `client_action_id` conflict checking (Ragul).
* **RFC 9457 Errors**: Native problem details error handling (`app.core.errors`).
* **Tests**: 106/106 unit, contract, and workflow tests passing across application, ORM models, API routes, and async service workflows.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.115 |
| Runtime | Python 3.12+ (tested on 3.14) |
| Validation | Pydantic v2 + pydantic-settings |
| ORM | SQLAlchemy 2.x (async) |
| Dev DB | SQLite + aiosqlite |
| Prod DB | PostgreSQL + PostGIS + asyncpg (drop-in migration) |
| Migrations | Alembic |
| Testing | pytest + pytest-asyncio + httpx |

---

## Quick Start

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env

# 4. Apply migrations
alembic upgrade head

# 5. Start dev server
uvicorn app.main:app --reload --port 8001
```

The API docs are available at **http://localhost:8001/docs**  
OpenAPI spec at **http://localhost:8001/openapi.json**

---

## Team Integration Boundaries

This backend core service exposes clean integration interfaces for team workstreams:

| Team Member | Workstream | Service & Module | Integration Boundary |
|-------------|------------|------------------|----------------------|
| **Akshaya** | AI / Segmentation | `ImageryService` / `app.integrations.ai` | `SegmentationProcessor.process_tile()` |
| **Arun** | Topology Engine | `ParcelService` / `app.integrations.topology` | `TopologyValidationService.validate_parcel()` |
| **Prajith** | Audit & Auth | `AuditEventService` / `app.routers.audit` | SHA-256 hash chaining (`prev_hash`/`entry_hash`) & JWT Auth |
| **Ragul** | Offline Sync | `ParcelService.sync_batch` / `SyncAction` | `POST /v1/parcels/sync` (persistent idempotency) |

---

## API Route Catalogue (`/v1`)

| Domain | Method | Path | Description |
|--------|--------|------|-------------|
| **Auth** | `POST` | `/v1/auth/token` | Obtain JWT token pair |
| | `POST` | `/v1/auth/refresh` | Refresh JWT token |
| **Imagery** | `POST` | `/v1/imagery/upload` | Ingest tile & queue processing |
| | `GET` | `/v1/imagery/jobs/{job_id}` | Poll processing job status |
| | `GET` | `/v1/imagery/tiles/{tile_id}` | Tile metadata |
| | `GET` | `/v1/imagery/tiles/{tile_id}/features` | AI-extracted features |
| **Parcels** | `GET` | `/v1/parcels` | List parcels (cursor-paginated) |
| | `GET` | `/v1/parcels/{parcel_id}` | Parcel detail |
| | `POST` | `/v1/parcels/{parcel_id}/edit` | Edit geometry |
| | `POST` | `/v1/parcels/{parcel_id}/approve` | Human approval |
| | `POST` | `/v1/parcels/{parcel_id}/reject` | Rejection |
| | `POST` | `/v1/parcels/sync` | Offline sync batch |
| **Validation** | `GET` | `/v1/validations/queue` | Validation queue |
| | `POST` | `/v1/validations/run` | Run validation batch |
| | `GET` | `/v1/parcels/{parcel_id}/flags` | Validation flags |
| **Conflicts** | `GET` | `/v1/conflicts` | List open conflicts |
| | `POST` | `/v1/conflicts/{conflict_id}/resolve` | Resolve conflict |
| **Change Detection** | `POST` | `/v1/change-detection/run` | Trigger tile comparison |
| | `GET` | `/v1/change-detection/{job_id}` | Job status |
| **Geographic** | `GET` | `/v1/geo/parcels` | GeoJSON FeatureCollection |
| **Exports** | `POST` | `/v1/exports` | Request export |
| | `GET` | `/v1/exports/{export_id}` | Export status & download |
| **Audit** | `GET` | `/v1/audit/{parcel_id}` | Parcel audit history |
| | `GET` | `/v1/audit/verify/{parcel_id}` | Verify hash chain |
| | `GET` | `/v1/audit/export/{batch_id}` | Audit batch export |
| **Metrics** | `GET` | `/v1/models/metrics` | AI model metrics |

---

## Verification & Testing

```bash
# 1. Compile check
python -m compileall app/ tests/ -q

# 2. Test suite
pytest -q

# 3. Export OpenAPI schema
python -c "import yaml; from app.main import app; yaml.dump(app.openapi(), open('openapi.yaml', 'w'), sort_keys=False)"
```
