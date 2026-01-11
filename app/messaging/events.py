"""Event payload schemas for messaging."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class PostCreatedEvent(BaseModel):
    post_id: UUID
    user_id: UUID
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None


class PostDeletedEvent(BaseModel):
    post_id: UUID
    user_id: UUID


class PostLikedEvent(BaseModel):
    post_id: UUID
    user_id: UUID
    occurred_at: datetime


class PostUnlikedEvent(BaseModel):
    post_id: UUID
    user_id: UUID
    occurred_at: datetime


class PostCommentedEvent(BaseModel):
    post_id: UUID
    comment_id: UUID
    user_id: UUID
    content: str
    occurred_at: datetime


class CommentDeletedEvent(BaseModel):
    post_id: UUID
    comment_id: UUID
    user_id: UUID
    occurred_at: datetime
