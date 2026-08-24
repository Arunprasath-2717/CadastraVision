"""
app/models/user.py
───────────────────
User ORM model.

Roles
─────
* admin    — full read/write, user management, audit log access
* analyst  — create and update parcels/records, no user management
* viewer   — read-only access to parcels and records

Passwords are NEVER stored in plain text. The ``hashed_password`` column
holds a bcrypt hash produced by ``app.core.security`` (Phase 3).

The ``email`` column is the primary login credential and carries a unique
index. ``full_name`` is free-form and not used for auth.
"""

from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class UserRole(str, enum.Enum):
    """Application roles — stored as VARCHAR so no DB enum type is needed."""

    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class User(UUIDMixin, TimestampMixin, Base):
    """Registered application user."""

    __tablename__ = "users"

    # ── Identity ──────────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(320),    # RFC 5321 max email length
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Access control ────────────────────────────────────────────────────────
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda e: [m.value for m in e], native_enum=False),
        default=UserRole.VIEWER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    uploaded_tiles: Mapped[list["ImageryTile"]] = relationship(  # noqa: F821
        "ImageryTile", back_populates="uploaded_by", lazy="select"
    )
    reviewed_parcels: Mapped[list["Parcel"]] = relationship(  # noqa: F821
        "Parcel", back_populates="reviewed_by", lazy="select"
    )
    audit_entries: Mapped[list["AuditLogEntry"]] = relationship(  # noqa: F821
        "AuditLogEntry", back_populates="user", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!r} email={self.email!r} role={self.role!r}>"
