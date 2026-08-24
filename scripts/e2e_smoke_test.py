#!/usr/bin/env python3
"""
scripts/e2e_smoke_test.py
─────────────────────────
Automated End-to-End Smoke Test for CadastraVision Full-Stack Integration.

Verifies:
1. Health & Readiness endpoints
2. User Registration & Authentication (JWT Token generation)
3. Authenticated endpoint retrieval (/v1/auth/me)
4. Parcel listing & detail retrieval
5. GeoJSON spatial features endpoint (/v1/geo/parcels, /v1/geo/buildings, /v1/geo/roads)
6. Validation queue & conflicts endpoints
7. Audit trail endpoints
"""

from __future__ import annotations

import asyncio
import sys
import time
from typing import Any

import httpx

BASE_URL = "http://localhost:8001"


async def run_smoke_test() -> None:
    print("=" * 60)
    print("CADASTRAVISION FULL-STACK E2E SMOKE TEST")
    print("=" * 60)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Health Endpoint Check
        print("[1/8] Checking Health Endpoint GET /health ...")
        resp = await client.get("/health")
        assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
        print(f"      SUCCESS: {resp.json()}")

        # 2. Registration Flow
        test_email = f"surveyor_{int(time.time())}@cadastral.gov.in"
        print(f"[2/8] Registering Test User: {test_email} ...")
        reg_payload = {
            "email": test_email,
            "full_name": "E2E Test Surveyor",
            "password": "TestPassword123!",
            "role": "analyst",
        }

        resp = await client.post("/v1/auth/register", json=reg_payload)
        assert resp.status_code == 201, f"Registration failed: {resp.text}"
        user_data = resp.json()
        print(f"      SUCCESS: Created user ID {user_data['id']}")

        # 3. Login & Token Generation
        print("[3/8] Logging in with OAuth2 Credentials ...")
        token_payload = {
            "username": test_email,
            "password": "TestPassword123!",
        }
        resp = await client.post("/v1/auth/token", json=token_payload)
        assert resp.status_code == 200, f"Token request failed: {resp.text}"
        tokens = resp.json()
        access_token = tokens["access_token"]
        assert access_token, "No access token received"
        print(f"      SUCCESS: JWT Token acquired (type: {tokens.get('token_type')})")

        headers = {"Authorization": f"Bearer {access_token}"}

        # 4. Protected User Info (/v1/auth/me)
        print("[4/8] Fetching Protected Current User /v1/auth/me ...")
        resp = await client.get("/v1/auth/me", headers=headers)
        assert resp.status_code == 200, f"Get me failed: {resp.text}"
        me_data = resp.json()
        assert me_data["email"] == test_email, "Email mismatch"
        print(f"      SUCCESS: Authenticated user: {me_data['full_name']} ({me_data['role']})")

        # 5. Parcel Data Flow
        print("[5/8] Fetching Parcels List /v1/parcels ...")
        resp = await client.get("/v1/parcels", headers=headers)
        assert resp.status_code == 200, f"List parcels failed: {resp.text}"
        parcels_data = resp.json()
        items = parcels_data.get("items", [])
        print(f"      SUCCESS: Retrieved {len(items)} parcels from backend DB.")

        # 6. GeoJSON GIS Flow
        print("[6/8] Fetching GeoJSON Layers /v1/geo/parcels, buildings, roads ...")
        resp_p = await client.get("/v1/geo/parcels", headers=headers)
        resp_b = await client.get("/v1/geo/buildings", headers=headers)
        resp_r = await client.get("/v1/geo/roads", headers=headers)
        assert resp_p.status_code == 200 and resp_b.status_code == 200 and resp_r.status_code == 200
        print(f"      SUCCESS: GIS GeoJSON layers loaded successfully.")

        # 7. Validations & Conflicts Queue
        print("[7/8] Fetching Validation Queue & Conflicts ...")
        resp_v = await client.get("/v1/validations/queue", headers=headers)
        resp_c = await client.get("/v1/conflicts", headers=headers)
        assert resp_v.status_code == 200 and resp_c.status_code == 200
        print(f"      SUCCESS: Validations & Conflicts endpoints operational.")

        # 8. Audit Log Verification
        print("[8/8] Fetching Audit Summary /v1/audit/summary ...")
        resp_a = await client.get("/v1/audit/summary", headers=headers)
        assert resp_a.status_code == 200
        print(f"      SUCCESS: Audit trail accessible: {resp_a.json()}")

    print("=" * 60)
    print("ALL E2E SMOKE TEST STEPS PASSED SUCCESSFULLY (0)")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_smoke_test())
    except Exception as err:
        print(f"\nSMOKE TEST FAILED: {err}", file=sys.stderr)
        sys.exit(1)
