"""Common API response schemas."""

from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int
    offset: int
    limit: int
    has_more: bool


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    details: Optional[dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """Simple success response."""

    success: bool = True
    message: Optional[str] = None
