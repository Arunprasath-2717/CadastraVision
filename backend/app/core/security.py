"""
app/core/security.py
────────────────────
JWT token handling, password hashing, and FastAPI security dependencies.

Supports:
- Password hashing (bcrypt via passlib/bcrypt)
- Access and refresh JWT tokens (HMAC SHA-256 via pyjwt)
- Bearer token HTTP scheme for OpenAPI
- Dependency injection: get_current_user, get_current_active_user, require_role, require_permission
- RFC 9457 compliant error responses on auth failure
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import AuthenticationError, AuthorizationError, NotFoundError
from app.models.user import User, UserRole
import bcrypt

logger = logging.getLogger(__name__)
settings = get_settings()

security_scheme = HTTPBearer(auto_error=False)

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """Return bcrypt hash of plain password."""
    pw_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    try:
        pw_bytes = plain_password.encode("utf-8")
        h_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, h_bytes)
    except Exception:
        return False


def create_token(data: dict[str, Any], expires_delta: timedelta, token_type: str = "access") -> str:
    """Create a signed JWT with standard claims."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    to_encode.update({
        "exp": expire,
        "iat": now,
        "nbf": now,
        "type": token_type,
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_access_token(user_id: str, email: str, role: str, expires_delta: timedelta | None = None) -> str:
    """Create a short-lived access token."""
    delta = expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_token({"sub": user_id, "email": email, "role": role}, delta, token_type="access")


def create_refresh_token(user_id: str, email: str, role: str, expires_delta: timedelta | None = None) -> str:
    """Create a long-lived refresh token."""
    delta = expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return create_token({"sub": user_id, "email": email, "role": role}, delta, token_type="refresh")


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """
    Decode and validate a JWT.
    Raises AuthenticationError if signature, expiration, algorithm, or type is invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "iat", "sub", "type"]}
        )
        if payload.get("type") != expected_type:
            raise AuthenticationError(f"Invalid token type: expected '{expected_type}'")
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    FastAPI dependency to extract and verify JWT from Authorization header.
    Returns the User model or raises AuthenticationError (HTTP 401 RFC 9457).
    """
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Authentication token is missing")

    token = credentials.credentials
    payload = decode_token(token, expected_type="access")
    user_id: str = payload.get("sub", "")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user is None:
        raise AuthenticationError("User account not found")

    if not user.is_active:
        raise AuthenticationError("User account is inactive")

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure current authenticated user is active."""
    if not current_user.is_active:
        raise AuthenticationError("User account is inactive")
    return current_user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory to enforce role-based access control (RBAC).
    Raises AuthorizationError (HTTP 403 RFC 9457) if user's role is not permitted.
    """
    async def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in allowed_roles:
            raise AuthorizationError(
                f"Role '{current_user.role.value}' is not authorized. Allowed: {[r.value for r in allowed_roles]}"
            )
        return current_user

    return role_checker


# Role -> Permissions Mapping Matrix
ROLE_PERMISSIONS: dict[UserRole, set[str]] = {
    UserRole.ADMIN: {
        "read:imagery", "write:imagery", "process:imagery", "retry:imagery",
        "read:parcels", "write:parcels", "approve:parcels", "delete:parcels",
        "read:validations", "resolve:validations",
        "read:audit", "write:users", "sync:offline"
    },
    UserRole.ANALYST: {
        "read:imagery", "write:imagery", "process:imagery", "retry:imagery",
        "read:parcels", "write:parcels", "approve:parcels",
        "read:validations", "resolve:validations",
        "read:audit", "sync:offline"
    },
    UserRole.VIEWER: {
        "read:imagery", "read:parcels", "read:validations", "read:audit"
    },
}


def require_permission(permission: str):
    """
    Dependency factory to enforce fine-grained action permission.
    Raises AuthorizationError (HTTP 403 RFC 9457) if user lacks permission.
    """
    async def permission_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        user_perms = ROLE_PERMISSIONS.get(current_user.role, set())
        if permission not in user_perms:
            raise AuthorizationError(
                f"Permission '{permission}' denied for role '{current_user.role.value}'"
            )
        return current_user

    return permission_checker
