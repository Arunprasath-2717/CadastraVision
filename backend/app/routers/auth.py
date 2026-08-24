"""
app/routers/auth.py
────────────────────
POST /v1/auth/token
POST /v1/auth/refresh

STUB: Returns schema-valid placeholder responses.
Real JWT implementation is Prajith's workstream (Phase 3 integration).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.auth import RefreshRequest, TokenRequest, TokenResponse

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Obtain access token",
    description=(
        "Exchange credentials for a JWT access + refresh token pair. "
        "**STUB** — real JWT implementation: Prajith (Phase 3)."
    ),
)
async def get_token(body: TokenRequest) -> TokenResponse:
    # INTEGRATION STUB — Prajith wires real auth here
    return TokenResponse(
        access_token="STUB_ACCESS_TOKEN",
        refresh_token="STUB_REFRESH_TOKEN",
        token_type="bearer",
        expires_in=3600,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Exchange a refresh token for a new token pair. **STUB** — Phase 3.",
)
async def refresh_token(body: RefreshRequest) -> TokenResponse:
    # INTEGRATION STUB
    return TokenResponse(
        access_token="STUB_NEW_ACCESS_TOKEN",
        refresh_token=body.refresh_token,
        token_type="bearer",
        expires_in=3600,
    )
