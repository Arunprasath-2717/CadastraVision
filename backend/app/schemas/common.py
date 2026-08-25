"""
app/schemas/common.py
──────────────────────
Shared Pydantic schemas: pagination and RFC 9457 problem details.

Used across all routers — import from here, not from individual schema files.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard cursor-based paginated response.

    PRD contract:
        GET /v1/parcels?cursor=<cursor>&limit=<n>
        → {"items": [...], "next_cursor": "<token>" | null}
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: list[T]
    next_cursor: str | None = Field(
        default=None,
        description="Opaque cursor token for the next page. Null when no more pages.",
    )


class ProblemDetail(BaseModel):
    """
    RFC 9457 Problem Details for HTTP APIs.

    https://www.rfc-editor.org/rfc/rfc9457
    """

    type: str = Field(description="URI identifying the problem type")
    title: str = Field(description="Short, human-readable summary")
    status: int = Field(description="HTTP status code")
    detail: str = Field(description="Human-readable explanation of the specific occurrence")
    instance: str | None = Field(
        default=None,
        description="URI identifying the specific occurrence of the problem",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "https://cadastravision.io/errors/not-found",
                "title": "Not Found",
                "status": 404,
                "detail": "Parcel 'abc-123' was not found.",
                "instance": "/v1/parcels/abc-123",
            }
        }
    )
