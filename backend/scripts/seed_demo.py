#!/usr/bin/env python3
"""
scripts/seed_demo.py
──────────────────────
Idempotent development database seeder.
Seeds demo users, parcels, validation flags, and conflicts if absent.

Usage:
    PYTHONPATH=. python scripts/seed_demo.py
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, engine
from app.core.logging import get_logger, setup_logging
from app.core.security import hash_password
from app.models.audit import AuditAction, AuditLogEntry
from app.models.conflict import Conflict, ConflictStatus, ConflictType
from app.models.parcel import Parcel, ParcelWorkflowStatus
from app.models.user import User, UserRole
from app.models.validation import FlagSeverity, FlagType, ValidationFlag

setup_logging()
logger = get_logger(__name__)


async def seed_demo_data() -> None:
    logger.info("Starting idempotent demo data seeding...")

    async with AsyncSessionLocal() as session:
        # 1. Seed Users
        surveyor_email = "muthulakshmi@cadastral.gov.in"
        res = await session.execute(select(User).where(User.email == surveyor_email))
        surveyor = res.scalar_one_or_none()

        if not surveyor:
            surveyor = User(
                id="USR-4092",
                email=surveyor_email,
                full_name="Muthulakshmi S.",
                hashed_password=hash_password("SurveyorPassword123!"),
                role=UserRole.ANALYST,
                is_active=True,
            )
            session.add(surveyor)
            logger.info("Seeded surveyor user: %s", surveyor_email)
        else:
            logger.info("Surveyor user already exists: %s", surveyor_email)

        admin_email = "admin@cadastravision.org"
        res = await session.execute(select(User).where(User.email == admin_email))
        admin = res.scalar_one_or_none()

        if not admin:
            admin = User(
                id="USR-0001",
                email=admin_email,
                full_name="System Administrator",
                hashed_password=hash_password("AdminPassword123!"),
                role=UserRole.ADMIN,
                is_active=True,
            )
            session.add(admin)
            logger.info("Seeded admin user: %s", admin_email)

        await session.commit()

        # 2. Seed Parcels
        demo_parcels = [
            {
                "id": "PCL-7821",
                "geometry_wkt": "POLYGON((77.5946 12.9716, 77.5956 12.9716, 77.5956 12.9726, 77.5946 12.9726, 77.5946 12.9716))",
                "source_tile_id": None,
                "confidence": 0.94,
                "zone": "East Zone",
                "jurisdiction": "Bengaluru East Municipal Corp",
                "workflow_status": ParcelWorkflowStatus.VALIDATED,
            },
            {
                "id": "PCL-7822",
                "geometry_wkt": "POLYGON((77.5957 12.9716, 77.5967 12.9716, 77.5967 12.9726, 77.5957 12.9726, 77.5957 12.9716))",
                "source_tile_id": None,
                "confidence": 0.72,
                "zone": "East Zone",
                "jurisdiction": "Bengaluru East Municipal Corp",
                "workflow_status": ParcelWorkflowStatus.VALIDATION_PENDING,
            },
            {
                "id": "PCL-7823",
                "geometry_wkt": "POLYGON((77.5968 12.9716, 77.5978 12.9716, 77.5978 12.9726, 77.5968 12.9726, 77.5968 12.9716))",
                "source_tile_id": None,
                "confidence": 0.98,
                "zone": "South Zone",
                "jurisdiction": "Bengaluru South Municipal Corp",
                "workflow_status": ParcelWorkflowStatus.APPROVED,
            },
        ]

        for p_data in demo_parcels:
            res = await session.execute(
                select(Parcel).where(Parcel.id == p_data["id"])
            )
            if not res.scalar_one_or_none():
                parcel = Parcel(**p_data)
                session.add(parcel)
                logger.info("Seeded demo parcel: %s", p_data["id"])

        await session.commit()

        # 3. Seed Validation Flags & Conflicts
        flag_id = "FLG-7822-01"
        res = await session.execute(
            select(ValidationFlag).where(ValidationFlag.id == flag_id)
        )
        if not res.scalar_one_or_none():
            flag = ValidationFlag(
                id=flag_id,
                parcel_id="PCL-7822",
                flag_type=FlagType.OVERLAP,
                severity=FlagSeverity.WARNING,
                description="Minor boundary overlap detected with adjacent parcel PCL-7821",
                resolved=False,
            )
            session.add(flag)
            logger.info("Seeded validation flag: %s", flag_id)

        conflict_id = "CNF-7822-01"
        res = await session.execute(
            select(Conflict).where(Conflict.id == conflict_id)
        )
        if not res.scalar_one_or_none():
            conflict = Conflict(
                id=conflict_id,
                parcel_a_id="PCL-7821",
                parcel_b_id="PCL-7822",
                conflict_type=ConflictType.OVERLAP,
                status=ConflictStatus.OPEN,
            )
            session.add(conflict)
            logger.info("Seeded conflict record: %s", conflict_id)

        # 4. Seed Audit Record
        audit_id = "AUD-INIT-001"
        res = await session.execute(
            select(AuditLogEntry).where(AuditLogEntry.id == audit_id)
        )
        if not res.scalar_one_or_none():
            audit = AuditLogEntry(
                id=audit_id,
                user_id="USR-0001",
                entity_type="system",
                entity_id="database",
                action=AuditAction.CREATE,
                diff_json={"event": "initial_demo_seed", "status": "completed"},
                prev_hash="GENESIS_HASH_00000000000000000000000000000000",
                entry_hash="9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e",
            )

            session.add(audit)
            logger.info("Seeded audit log entry: %s", audit_id)

        await session.commit()
        logger.info("Demo data seeding completed successfully.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
