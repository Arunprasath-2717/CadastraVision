# CadastraVision Backend — Core Service (PRD-CM-03)

Production-ready **FastAPI** backend for the CadastralMap AI-enabled automated cadastral mapping platform (**SIH 2026, PS 26012**).

## Status: Phase 8 Complete (Production Integration, Real AI/Geospatial Engines & Deployment)

* **280/280 Tests Passing**: 100% test coverage across Phase 1–8 (Foundation, Domain Models, Workflows, AI Integration, Security & RBAC, Change Detection & Secure Export, Hardening, and Production Integration).
* **Real Topology Engine**: Powered by `Shapely` / GEOS for geometry validity, self-intersection, overlapping polygon checks, duplicate geometry detection, and non-destructive geometry repair.
* **AI Provider Adapter Architecture**: `AIProviderInterface` abstract base class supporting `MockSegmentationProvider` (deterministic integration testing) and `YOLOv8SegmentationProvider` (production YOLOv8/SAM model adapter) with metadata traceability (`model_name`, `model_version`, `processing_time_s`).
* **Async Background Processing**: `JobQueue` and `BackgroundJobWorker` handling background jobs with idempotency duplicate prevention, timeout handling, and automatic retries.
* **Storage Abstraction Layer**: Unified `StorageService` supporting `LocalStorageProvider` and `S3StorageProvider` interface with strict path-traversal safeguards and virtual URI mapping.
* **PostgreSQL & PostGIS Readiness**: Async PostgreSQL driver (`asyncpg`) and WGS84 CRS (EPSG:4326) documentation.
* **Docker Deployment**: Multi-stage, non-root `Dockerfile` verified via `docker build`.
* **Tamper-Evident SHA-256 Audit Trail**: Cryptographic hash chaining maintained across all operations.

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

## API Route Catalogue (`/v1`)

| Domain | Method | Path | Description |
|--------|--------|------|-------------|
| **Auth** | `POST` | `/v1/auth/token` | Obtain JWT token pair |
| | `POST` | `/v1/auth/refresh` | Refresh JWT token |
| **Config** | `GET` | `/v1/config/database` | Database connection status & tables |
| | `POST` | `/v1/config/database/init` | Initialize database schema & tables |
| **Imagery** | `POST` | `/v1/imagery/upload` | Ingest tile & queue processing |
| | `GET` | `/v1/imagery/jobs/{job_id}` | Poll processing job status |
| | `POST` | `/v1/imagery/jobs/{job_id}/retry` | Retry failed/queued processing job safely |
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
| **Change Detection** | `POST` | `/v1/change-detection/jobs` | Trigger feature change detection |
| | `GET` | `/v1/change-detection/jobs/{job_id}` | Poll change detection status |
| | `GET` | `/v1/change-detection/results/{job_id}` | Retrieve detected changes |
| | `POST` | `/v1/changes/{change_id}/approve` | Approve change candidate (Analyst/Admin) |
| | `POST` | `/v1/changes/{change_id}/reject` | Reject change candidate (Analyst/Admin) |
| **Geographic** | `GET` | `/v1/geo/parcels` | GeoJSON FeatureCollection |
| **Exports** | `POST` | `/v1/exports` | Request export (GeoJSON, CSV, JSON) |
| | `GET` | `/v1/exports/{export_id}` | Export status & download URL |
| | `GET` | `/v1/exports/{export_id}/download` | Download export payload file |
| **Audit** | `GET` | `/v1/audit/{parcel_id}` | Parcel audit history |
| | `GET` | `/v1/audit/verify/{parcel_id}` | Verify hash chain integrity |
| | `GET` | `/v1/audit/export/{batch_id}` | Audit batch export |
| **Metrics** | `GET` | `/v1/models/metrics` | AI model metrics |

---

## Verification & Testing

```bash
# 1. Compile check
python -m compileall app/ tests/ -q

# 2. Test suite (227 tests)
pytest -q
```
