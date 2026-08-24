"""app/schemas/auth.py — Authentication request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class TokenRequest(BaseModel):
    """POST /v1/auth/token — credential exchange."""
    username: str = Field(description="User email address")
    password: str = Field(description="User password")

    model_config = {"json_schema_extra": {"example": {"username": "user@example.com", "password": "secret"}}}


class TokenResponse(BaseModel):
    """Successful authentication response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token TTL in seconds")


class RefreshRequest(BaseModel):
    """POST /v1/auth/refresh — refresh token exchange."""
    refresh_token: str
