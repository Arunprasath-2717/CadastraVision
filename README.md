# 🗺️ CadastraVision

### AI-Powered Cadastral Intelligence Platform

CadastraVision is a GIS + AI platform for **parcel mapping, spatial checking, change detection and surveyor review**.

> **Our idea:** Let AI find possible problems faster, while the surveyor keeps the final decision.

---

## 🎯 Problem

Cadastral work can become difficult when surveyors manually compare:

- Parcel boundaries
- Buildings and roads
- Old and new spatial data
- Survey information and imagery
- Land-use changes

It is also difficult to work in low-connectivity areas and maintain a clear history of changes.

## 💡 Our Solution

CadastraVision brings these tasks into one workflow:

**Data → GIS Map → AI/Spatial Analysis → Anomaly → Risk/Confidence → Surveyor Review → Validated Record**

It is mainly a **decision-support tool**. AI does not directly overwrite important land records.

---

## ⭐ Main Features

| Feature | What it does |
|---|---|
| 🗺️ GIS Command Center | Shows parcels, buildings, roads and other layers |
| 📡 Data Ingestion | Handles spatial/cadastral data and imagery workflows |
| 🤖 AI Intelligence | Helps identify possible spatial anomalies |
| 🔍 Change Detection | Finds possible boundary/building/land-use changes |
| ✅ Surveyor Review | Lets a human verify, edit or escalate findings |
| 📊 Analytics | Shows parcel, building, validation and confidence metrics |
| 🕒 Property History | Shows important changes as a timeline |
| 📄 Reports | Creates parcel summaries and exportable information |
| 📴 Offline Support | Keeps supported actions locally until connection returns |
| 🔐 Security | JWT authentication, RBAC and audit logging |

---

## 🖥️ Application

### 1. Command Center
The main workspace for surveyors: interactive map, layer controls, parcel inspection, data upload, review queue, quick actions and AI assistance. The map can be expanded when more space is needed.

### 2. AI Intelligence
Users can ask spatial questions such as:
- Find parcels with boundary anomalies
- Find overlapping building footprints
- Find possible land-use changes

Results include **confidence, risk, explanation and recommendation**.

### 3. Surveyor Review
AI findings are sent to a review queue. The surveyor checks the **parcel, issue, severity, confidence and spatial details**, then accepts, edits or escalates the finding.

### 4. Spatial Analytics
Shows parcel/building counts, road coverage, validation progress, confidence distribution, AI detection statistics and spatial trends.

### 5. Property History
Shows important parcel events such as boundary realignment, building expansion, access-lane changes and land-use updates.

### 6. Cadastral Reports
Creates structured summaries with parcel details, AI findings, validation results, surveyor decisions and change summaries.

---

## 🔄 How the System Works

```text
Spatial / Cadastral Data
          ↓
     Data Ingestion
          ↓
     GIS Visualization
          ↓
   AI + Spatial Analysis
          ↓
    Anomaly Detection
          ↓
  Risk / Confidence Score
          ↓
      Surveyor Review
        ↙       ↘
    Accept     Edit/Escalate
        ↘       ↙
     Validated Record
          ↓
 History • Analytics • Reports
          ↓
       Audit Trail
```

---

## 🧠 AI + GIS Pipeline

```text
Drone / Spatial Imagery
          ↓
     Preprocessing
          ↓
 Feature / Object Analysis
          ↓
Parcel + Building Geometry
          ↓
    Change Detection
          ↓
 Topological Validation
          ↓
 Confidence / Risk Score
          ↓
     Surveyor Review
```

The repository includes **FastSAM** and **YOLOv8 segmentation model assets**.

The current full-system baseline keeps heavy AI runtime dependencies separate from the main deterministic application, so the GIS/database workflow can run independently.

---

## 🗺️ GIS Layer

- **MapLibre GL** – map rendering
- **OpenFreeMap** – vector basemap
- **OpenStreetMap / Overpass API** – spatial data
- **GeoJSON** – spatial data exchange
- **Shapely** – geometry processing
- Parcel, building, road and field layers
- Coordinate reference system handling

---

## 📴 Offline Workflow

```text
ONLINE
Frontend → FastAPI → Database

OFFLINE
Frontend → Local Storage → Pending Queue
                         ↓
                  Connection Restored
                         ↓
                       Sync
```

Supported field actions can therefore be retained locally and synchronized later.

---

## 🔐 Security

- JWT authentication
- Role-Based Access Control (RBAC)
- Protected API endpoints
- Input/schema validation
- CORS configuration
- Security headers
- Audit logging
- SHA-256 audit chaining

---

## 🏗️ Architecture

```text
 React + Vite Frontend
          │
       REST API
       + JWT Auth
          │
          ▼
     FastAPI Backend
          │
    ┌─────┼─────────┐
    │     │         │
   Auth   GIS    Validation
    │     │         │
    └─────┼─────────┘
          ▼
    SQLAlchemy Layer
          │
          ▼
 SQLite (Development)
        /
 PostgreSQL + PostGIS
      (Target)
```

---

## 🛠️ Tech Stack

**Frontend:** React, Vite, JavaScript, Tailwind CSS, MapLibre GL, PWA/local persistence

**Backend:** Python, FastAPI, Pydantic, SQLAlchemy, Alembic, JWT, Shapely

**Database:** SQLite for local development; PostgreSQL + PostGIS for spatial deployment

**AI/GIS:** FastSAM, YOLOv8 segmentation, MapLibre GL, OpenFreeMap, OpenStreetMap, Overpass API, GeoJSON

---

## 📂 Project Structure

```text
CadastraVision/
├── ai/                  # AI components
├── ai-service/          # AI service layer
├── backend/             # FastAPI backend
├── database/            # Database resources
├── docs/                # Documentation
├── frontend/            # React application
├── infrastructure/      # Deployment files
├── scripts/              # Utility scripts
├── tests/                # Tests
├── docker-compose.yml
├── FastSAM-s.pt
├── yolov8n-seg.pt
└── README.md
```

---

## 🚀 Run Locally

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8001
```

API: `http://localhost:8001`

Swagger: `http://localhost:8001/docs`

### Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Vite will show the frontend URL, normally `http://localhost:5173`.

### Docker

If Docker is available:

```bash
docker compose up --build
```

---

## 🔌 Backend API

FastAPI provides interactive Swagger documentation.

Main API areas:

```text
Health
Authentication
Users / Roles
Cadastral Data
GIS / Spatial Operations
Validation
History / Audit
Reports / Exports
```

---

## 🚀 What Makes It Different?

CadastraVision is not just a:

**Map Viewer + AI Model + Database**

It connects:

```text
GIS
 +
AI / Spatial Analysis
 +
Validation
 +
Human Review
 +
Offline Support
 +
Auditability
        ↓
  CadastraVision
```

The key idea is **human-in-the-loop validation**: AI finds and prioritizes possible issues, while the surveyor controls the final decision.

---

## 🌱 Future Scope

- Full production AI inference
- Larger drone/satellite imagery pipelines
- Better cadastral change detection
- Orthomosaic processing
- Mobile field-surveyor workflows
- Government land-record integration
- Large-scale PostGIS deployment
- More explainable AI

---

## 🇮🇳 Smart India Hackathon 2026

**CadastraVision — AI-Powered Cadastral Intelligence**

**Goal:** Make cadastral work faster, easier to review and more traceable using GIS, AI and human validation.

> **GIS intelligence with humans in control.**
