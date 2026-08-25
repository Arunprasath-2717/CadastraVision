"""app/schemas/auth.py — Authentication request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.user import UserRole
from app.schemas.user import UserResponse


class TokenRequest(BaseModel):
    """POST /v1/auth/token or POST /v1/auth/login — credential exchange."""
    username: str = Field(description="User email address")
    password: str = Field(description="User password")

    model_config = {"json_schema_extra": {"example": {"username": "admin@cadastravision.org", "password": "AdminPassword123!"}}}


class LoginRequest(BaseModel):
    """POST /v1/auth/login request schema."""
    email: str = Field(description="User email address")
    password: str = Field(description="User password")

    model_config = {"json_schema_extra": {"example": {"email": "admin@cadastravision.org", "password": "AdminPassword123!"}}}


class TokenResponse(BaseModel):
    """Successful authentication token pair response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token TTL in seconds")
    user: UserResponse | None = Field(default=None, description="Authenticated user info")


class RefreshRequest(BaseModel):
    """POST /v1/auth/refresh — refresh token exchange."""
    refresh_token: str
