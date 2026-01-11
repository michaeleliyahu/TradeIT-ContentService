"""Pydantic schema for post engagement stats."""
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class PostStatsResponse(BaseModel):
    """Represents aggregated engagement counters for a post."""

    post_id: UUID
    likes_count: int
    comments_count: int

    model_config = ConfigDict(from_attributes=True)
