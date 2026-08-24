"""app/schemas/user.py — User request and response Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    """POST /v1/auth/register request payload."""
    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=8, description="User password (min 8 chars)")
    full_name: str | None = Field(default=None, description="Full name of the user")
    role: UserRole = Field(default=UserRole.VIEWER, description="Requested role")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SuperSecretPassword123!",
                "full_name": "Jane Doe",
                "role": "analyst",
            }
        }
    )


class UserResponse(BaseModel):
    """
    Public user representation.
    NEVER exposes hashed_password or secrets.
    """
    id: str
    email: EmailStr
    full_name: str | None = None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
