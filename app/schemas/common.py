# app/schemas/common.py
"""Common schemas used across multiple modules."""
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, Optional
from math import ceil

T = TypeVar('T')

class PaginationMetadata(BaseModel):
    """Pagination metadata for list responses."""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")

class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper.

    Usage:
        PaginatedResponse[ProjectSummary](
            data=[...],
            metadata=PaginationMetadata(...)
        )
    """
    data: List[T] = Field(..., description="List of items for current page")
    metadata: PaginationMetadata = Field(..., description="Pagination metadata")

    class Config:
        from_attributes = True

def create_pagination_metadata(
    total: int,
    page: int,
    page_size: int
) -> PaginationMetadata:
    """
    Helper function to create pagination metadata.

    Args:
        total: Total number of items
        page: Current page number (1-indexed)
        page_size: Number of items per page

    Returns:
        PaginationMetadata object
    """
    total_pages = ceil(total / page_size) if page_size > 0 else 0

    return PaginationMetadata(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    )

class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")

class SuccessResponse(BaseModel):
    """Standard success response for operations that don't return data."""
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Optional[dict] = Field(None, description="Optional additional data")
