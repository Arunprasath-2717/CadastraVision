"""
tests/test_security.py
───────────────────────
Phase 5 Security Test Suite:
Comprehensive verification of authentication, authorization, RBAC, IDOR protection,
RFC 9457 error formatting, audit actor tracking, and hash-chain integrity.
"""

from __future__ import annotations

import uuid
from datetime import timedelta, datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.audit import AuditAction, AuditLogEntry
from app.models.imagery import ImageryTile, ProcessingJob, TileSource, JobStatus, JobType
from app.models.parcel import Parcel, ParcelWorkflowStatus
from app.models.user import User, UserRole
from app.services.audit_service import AuditService, GENESIS_HASH

settings = get_settings()


@pytest_asyncio.fixture
async def setup_test_users(db_session: AsyncSession):
    """Seed test users with different roles safely."""
    async def get_or_create_user(email: str, role: UserRole, full_name: str, active: bool = True) -> User:
        stmt = select(User).where(User.email == email)
        u = (await db_session.execute(stmt)).scalars().first()
        if not u:
            u = User(
                id=str(uuid.uuid4()),
                email=email,
                hashed_password=hash_password("TestPassword123!"),
                full_name=full_name,
                role=role,
                is_active=active,
            )
            db_session.add(u)
            await db_session.flush()
        return u

    admin = await get_or_create_user("admin_sec@example.com", UserRole.ADMIN, "Admin User")
    analyst = await get_or_create_user("analyst_sec@example.com", UserRole.ANALYST, "Analyst User")
    viewer = await get_or_create_user("viewer_sec@example.com", UserRole.VIEWER, "Viewer User")
    inactive = await get_or_create_user("inactive_sec@example.com", UserRole.VIEWER, "Inactive User", active=False)

    return {"admin": admin, "analyst": analyst, "viewer": viewer, "inactive": inactive}


@pytest.mark.anyio
async def test_01_successful_login(unauth_client: AsyncClient, setup_test_users: dict):
    admin = setup_test_users["admin"]
    resp = await unauth_client.post(
        "/v1/auth/login",
        json={"email": admin.email, "password": "TestPassword123!"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == admin.email


@pytest.mark.anyio
async def test_02_invalid_credentials(unauth_client: AsyncClient, setup_test_users: dict):
    admin = setup_test_users["admin"]
    resp = await unauth_client.post(
        "/v1/auth/login",
        json={"email": admin.email, "password": "WrongPassword!"},
    )
    assert resp.status_code == 401
    assert resp.json()["status"] == 401
    assert resp.json()["title"] == "Unauthorized"


@pytest.mark.anyio
async def test_03_missing_authentication(unauth_client: AsyncClient):
    resp = await unauth_client.get("/v1/parcels")
    assert resp.status_code == 401
    assert resp.headers["content-type"] == "application/problem+json"


@pytest.mark.anyio
async def test_04_invalid_jwt(unauth_client: AsyncClient):
    headers = {"Authorization": "Bearer INVALID.JWT.TOKEN"}
    resp = await unauth_client.get("/v1/parcels", headers=headers)
    assert resp.status_code == 401
    assert "Invalid token" in resp.json()["detail"]


@pytest.mark.anyio
async def test_05_expired_jwt(unauth_client: AsyncClient, setup_test_users: dict):
    user = setup_test_users["viewer"]
    token = create_access_token(user.id, user.email, user.role.value, expires_delta=timedelta(seconds=-10))
    headers = {"Authorization": f"Bearer {token}"}
    resp = await unauth_client.get("/v1/parcels", headers=headers)
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_06_unauthorized_role(unauth_client: AsyncClient, setup_test_users: dict):
    viewer = setup_test_users["viewer"]
    token = create_access_token(viewer.id, viewer.email, viewer.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    # Viewer tries to approve a parcel
    resp = await unauth_client.post(
        f"/v1/parcels/{uuid.uuid4()}/approve",
        json={"notes": "Viewer approval attempt"},
        headers=headers,
    )
    assert resp.status_code == 403
    assert resp.json()["status"] == 403


@pytest.mark.anyio
async def test_07_authorized_role(unauth_client: AsyncClient, setup_test_users: dict, db_session: AsyncSession):
    analyst = setup_test_users["analyst"]
    p = Parcel(id=str(uuid.uuid4()), workflow_status=ParcelWorkflowStatus.VALIDATED)
    db_session.add(p)
    await db_session.commit()

    token = create_access_token(analyst.id, analyst.email, analyst.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await unauth_client.post(
        f"/v1/parcels/{p.id}/approve",
        json={"notes": "Analyst approval"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["workflow_status"] == "approved"


@pytest.mark.anyio
async def test_08_permission_denial(unauth_client: AsyncClient, setup_test_users: dict):
    viewer = setup_test_users["viewer"]
    token = create_access_token(viewer.id, viewer.email, viewer.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    # Viewer tries to export audit batch (Admin only)
    resp = await unauth_client.get("/v1/audit/export/batch-1", headers=headers)
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_09_idor_attempt(unauth_client: AsyncClient, setup_test_users: dict):
    user1 = setup_test_users["viewer"]
    token = create_access_token(user1.id, user1.email, user1.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    fake_id = str(uuid.uuid4())
    resp = await unauth_client.get(f"/v1/parcels/{fake_id}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_10_protected_imagery_endpoint(unauth_client: AsyncClient):
    resp = await unauth_client.get(f"/v1/imagery/tiles/{uuid.uuid4()}")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_11_protected_parcel_endpoint(unauth_client: AsyncClient):
    resp = await unauth_client.get(f"/v1/parcels/{uuid.uuid4()}")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_12_protected_processing_job(unauth_client: AsyncClient):
    resp = await unauth_client.get(f"/v1/imagery/jobs/{uuid.uuid4()}")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_13_unauthorized_retry(unauth_client: AsyncClient, setup_test_users: dict):
    viewer = setup_test_users["viewer"]
    token = create_access_token(viewer.id, viewer.email, viewer.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await unauth_client.post(f"/v1/imagery/jobs/{uuid.uuid4()}/retry", headers=headers)
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_14_offline_forged_user(unauth_client: AsyncClient, setup_test_users: dict):
    viewer = setup_test_users["viewer"]
    token = create_access_token(viewer.id, viewer.email, viewer.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    sync_body = {
        "actions": [
            {
                "client_action_id": str(uuid.uuid4()),
                "action_type": "edit",
                "parcel_id": str(uuid.uuid4()),
                "payload": {"geometry_wkt": "POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))"},
            }
        ]
    }
    resp = await unauth_client.post("/v1/parcels/sync", json=sync_body, headers=headers)
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_15_parcel_approval_authorization(unauth_client: AsyncClient, setup_test_users: dict, db_session: AsyncSession):
    admin = setup_test_users["admin"]
    p = Parcel(id=str(uuid.uuid4()), workflow_status=ParcelWorkflowStatus.DRAFT)
    db_session.add(p)
    await db_session.commit()

    token = create_access_token(admin.id, admin.email, admin.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await unauth_client.post(f"/v1/parcels/{p.id}/approve", json={"notes": "Approve draft"}, headers=headers)
    assert resp.status_code == 400 or resp.status_code == 422


@pytest.mark.anyio
async def test_16_parcel_rejection_authorization(unauth_client: AsyncClient, setup_test_users: dict, db_session: AsyncSession):
    admin = setup_test_users["admin"]
    p = Parcel(id=str(uuid.uuid4()), workflow_status=ParcelWorkflowStatus.VALIDATED)
    db_session.add(p)
    await db_session.commit()

    token = create_access_token(admin.id, admin.email, admin.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await unauth_client.post(f"/v1/parcels/{p.id}/reject", json={"reason": "Invalid boundary"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["workflow_status"] == "rejected"


@pytest.mark.anyio
async def test_17_audit_actor_identity(unauth_client: AsyncClient, setup_test_users: dict, db_session: AsyncSession):
    admin = setup_test_users["admin"]
    p = Parcel(id=str(uuid.uuid4()), workflow_status=ParcelWorkflowStatus.VALIDATED)
    db_session.add(p)
    await db_session.commit()

    token = create_access_token(admin.id, admin.email, admin.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    await unauth_client.post(f"/v1/parcels/{p.id}/approve", json={"notes": "Audit identity test"}, headers=headers)

    stmt = select(AuditLogEntry).where(AuditLogEntry.entity_id == p.id)
    entry = (await db_session.execute(stmt)).scalars().first()
    assert entry is not None
    assert entry.user_id == admin.id


@pytest.mark.anyio
async def test_18_audit_hash_chain_integrity(db_session: AsyncSession):
    audit_service = AuditService(db_session)
    e1 = await audit_service.record_entry(
        user_id="user1", entity_type="parcel", entity_id="p1", action=AuditAction.CREATE, diff={"name": "P1"}
    )
    await db_session.commit()

    e2 = await audit_service.record_entry(
        user_id="user2", entity_type="parcel", entity_id="p1", action=AuditAction.EDIT, diff={"name": "P1_edited"}
    )
    await db_session.commit()

    assert e2.prev_hash == e1.entry_hash


@pytest.mark.anyio
async def test_19_sensitive_information_not_returned(unauth_client: AsyncClient, setup_test_users: dict):
    admin = setup_test_users["admin"]
    token = create_access_token(admin.id, admin.email, admin.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await unauth_client.get("/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "hashed_password" not in body
    assert "password" not in body


@pytest.mark.anyio
async def test_20_authentication_error_uses_rfc9457(unauth_client: AsyncClient):
    resp = await unauth_client.get("/v1/parcels")
    assert resp.status_code == 401
    body = resp.json()
    assert body["status"] == 401
    assert "type" in body
    assert "title" in body
    assert "detail" in body


@pytest.mark.anyio
async def test_21_openapi_security_scheme(unauth_client: AsyncClient):
    resp = await unauth_client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "components" in schema
    assert "securitySchemes" in schema["components"]
    assert "HTTPBearer" in schema["components"]["securitySchemes"]


@pytest.mark.anyio
async def test_22_password_never_appears_in_response(unauth_client: AsyncClient, setup_test_users: dict):
    admin = setup_test_users["admin"]
    resp = await unauth_client.post(
        "/v1/auth/login",
        json={"email": admin.email, "password": "TestPassword123!"},
    )
    assert resp.status_code == 200
    text = resp.text
    assert "TestPassword123!" not in text
    assert admin.hashed_password not in text


@pytest.mark.anyio
async def test_23_jwt_secret_never_appears_in_responses(unauth_client: AsyncClient, setup_test_users: dict):
    admin = setup_test_users["admin"]
    resp = await unauth_client.post(
        "/v1/auth/login",
        json={"email": admin.email, "password": "TestPassword123!"},
    )
    assert settings.SECRET_KEY not in resp.text


@pytest.mark.anyio
async def test_24_mass_assignment_cannot_modify_protected_fields(unauth_client: AsyncClient, setup_test_users: dict, db_session: AsyncSession):
    analyst = setup_test_users["analyst"]
    p = Parcel(id=str(uuid.uuid4()), workflow_status=ParcelWorkflowStatus.DRAFT)
    db_session.add(p)
    await db_session.commit()

    token = create_access_token(analyst.id, analyst.email, analyst.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await unauth_client.post(
        f"/v1/parcels/{p.id}/edit",
        json={"geometry_wkt": "POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))", "workflow_status": "approved"},
        headers=headers,
    )
    # Mass assignment prevention either rejects unexpected field schema (422) or ignores field (200)
    assert resp.status_code in (200, 422)
    if resp.status_code == 200:
        assert resp.json()["workflow_status"] != "approved"
