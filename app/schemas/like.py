"""Pydantic schemas for like operations."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class LikeResponse(BaseModel):
    """Represents a like response payload."""

    id: UUID
    post_id: UUID
    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
