"""
app/routers/auth.py
────────────────────
Production Authentication API endpoints:
- POST /v1/auth/register : Register a new user
- POST /v1/auth/login    : Exchange email/password for JWT token pair
- POST /v1/auth/token    : Standard OAuth2 credential exchange endpoint
- POST /v1/auth/refresh  : Exchange refresh token for new access token
- GET  /v1/auth/me       : Get currently authenticated user details
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService, AuditAction

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new application user record.",
)
async def register(
    body: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    auth_service = AuthService(db)
    user = await auth_service.register_user(body)

    # Record security audit event
    audit_service = AuditService(db)
    await audit_service.record_entry(
        user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        action=AuditAction.CREATE,
        diff={"email": user.email, "role": user.role.value},
    )

    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate user with email and password, returning JWT access and refresh tokens.",
)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(body.email, body.password)
    tokens = auth_service.create_tokens_for_user(user)

    # Record login audit
    audit_service = AuditService(db)
    await audit_service.record_entry(
        user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        action=AuditAction.LOGIN,
        diff={"email": user.email},
    )

    return tokens


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Obtain access token (OAuth2 standard)",
    description="Exchange username (email) and password for JWT access and refresh tokens.",
)
async def get_token(
    body: TokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(body.username, body.password)
    return auth_service.create_tokens_for_user(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token pair.",
)
async def refresh_token(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    auth_service = AuthService(db)
    return await auth_service.refresh_tokens(body.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user details",
    description="Retrieve account details of the currently authenticated user.",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    return UserResponse.model_validate(current_user)
