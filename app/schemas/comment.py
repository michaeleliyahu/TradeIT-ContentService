"""Pydantic schemas for comment operations."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    """Incoming payload for comment creation."""

    content: str = Field(..., min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    """Represents a comment response payload."""

    id: UUID
    post_id: UUID
    user_id: UUID
    content: str
    created_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class CommentListResponse(BaseModel):
    """Paginated list of comments."""

    items: list[CommentResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
