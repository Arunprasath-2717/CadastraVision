"""
app/services/auth_service.py
─────────────────────────────
Authentication and User Management Service.
Handles registration, credential verification, JWT generation, and token refresh.
"""

from __future__ import annotations

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AuthenticationError, ConflictError, NotFoundError, ValidationError
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate, UserResponse

logger = logging.getLogger(__name__)


class AuthService:
    """Service encapsulating authentication, user creation, and token logic."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register_user(self, user_create: UserCreate) -> User:
        """Register a new user in the system."""
        # Check existing email
        stmt = select(User).where(User.email == user_create.email)
        existing = (await self.db.execute(stmt)).scalars().first()
        if existing:
            raise ConflictError(f"User with email '{user_create.email}' already exists.")

        user = User(
            email=user_create.email,
            hashed_password=hash_password(user_create.password),
            full_name=user_create.full_name,
            role=user_create.role,
            is_active=True,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        logger.info("Registered user %s (role: %s)", user.email, user.role.value)
        return user

    async def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate user credentials and return the active User model."""
        stmt = select(User).where(User.email == email)
        user = (await self.db.execute(stmt)).scalars().first()
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationError("User account is inactive.")

        return user

    def create_tokens_for_user(self, user: User) -> TokenResponse:
        """Generate access and refresh tokens for a verified user."""
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )
        refresh_token = create_refresh_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )

    async def refresh_tokens(self, refresh_token_str: str) -> TokenResponse:
        """Validate refresh token and issue new token pair."""
        payload = decode_token(refresh_token_str, expected_type="refresh")
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid refresh token payload.")

        stmt = select(User).where(User.id == user_id)
        user = (await self.db.execute(stmt)).scalars().first()
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive.")

        return self.create_tokens_for_user(user)
