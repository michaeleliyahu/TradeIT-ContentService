"""Repository for like persistence operations."""
from typing import Optional
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.like import Like


class LikeRepository:
    """Data access for likes."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_post_and_user(self, post_id: UUID, user_id: UUID) -> Optional[Like]:
        stmt = select(Like).where(Like.post_id == post_id, Like.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_like(self, post_id: UUID, user_id: UUID) -> Like:
        like = Like(post_id=post_id, user_id=user_id)
        self.session.add(like)
        await self.session.flush()
        return like

    async def delete_like(self, like: Like) -> None:
        await self.session.delete(like)

    async def delete_by_post(self, post_id: UUID) -> None:
        stmt = delete(Like).where(Like.post_id == post_id)
        await self.session.execute(stmt)
