from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import map as map_api
from app.api import admin as admin_api
from app.api import features as features_api
from app.api import validation as validation_api
from app.api import conflicts as conflicts_api

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CadastralMap API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(map_api.router, prefix="/api/map", tags=["map"])
app.include_router(admin_api.router, prefix="/api/admin", tags=["admin"])
app.include_router(features_api.router, prefix="/api/features", tags=["features"])
app.include_router(validation_api.router, prefix="/api/validation", tags=["validation"])
app.include_router(conflicts_api.router, prefix="/api/conflicts", tags=["conflicts"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
