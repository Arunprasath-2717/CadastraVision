"""
Models package — SQLAlchemy ORM models (PRD-CM-03 aligned).

Import order follows FK dependency chain:
  base → user → imagery → parcel → feature → validation → sync → audit → conflict → export

All imports here ensure every table is registered on Base.metadata
before create_all() or Alembic autogenerate is called.
"""

from app.models.base import Base  # noqa: F401

# FK layer 0 — no dependencies
from app.models.user import User, UserRole  # noqa: F401

# FK layer 1 — depends on User
from app.models.imagery import (  # noqa: F401
    ImageryTile, TileSource, TileStatus,
    ProcessingJob, JobType, JobStatus,
)

# FK layer 2 — depends on User + ImageryTile
from app.models.parcel import (  # noqa: F401
    Parcel, ParcelWorkflowStatus, ALLOWED_TRANSITIONS,
)

# FK layer 3 — depends on ImageryTile + ProcessingJob + Parcel
from app.models.feature import BuildingFootprint, FeatureType  # noqa: F401
from app.models.change import ChangeRecord, ChangeType, ChangeStatus  # noqa: F401

# FK layer 3 — depends on Parcel
from app.models.validation import ValidationFlag, FlagType, FlagSeverity  # noqa: F401
from app.models.sync import SyncAction, SyncActionStatus  # noqa: F401
from app.models.conflict import Conflict, ConflictType, ConflictStatus  # noqa: F401

# FK layer 3 — depends on User
from app.models.audit import AuditLogEntry, AuditAction  # noqa: F401
from app.models.export import Export, ExportFormat, ExportStatus  # noqa: F401

__all__ = [
    "Base",
    "User", "UserRole",
    "ImageryTile", "TileSource", "TileStatus",
    "ProcessingJob", "JobType", "JobStatus",
    "Parcel", "ParcelWorkflowStatus", "ALLOWED_TRANSITIONS",
    "BuildingFootprint", "FeatureType",
    "ChangeRecord", "ChangeType", "ChangeStatus",
    "ValidationFlag", "FlagType", "FlagSeverity",
    "SyncAction", "SyncActionStatus",
    "AuditLogEntry", "AuditAction",
    "Conflict", "ConflictType", "ConflictStatus",
    "Export", "ExportFormat", "ExportStatus",
]
