"""Repository for post engagement stats operations."""
from typing import Optional
from uuid import UUID
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.post_content_stats import PostContentStats


class StatsRepository:
    """Data access for post engagement counters."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, post_id: UUID) -> Optional[PostContentStats]:
        stmt = select(PostContentStats).where(PostContentStats.post_id == post_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def ensure_stats(self, post_id: UUID) -> PostContentStats:
        stats = await self.get(post_id)
        if stats:
            return stats
        stats = PostContentStats(post_id=post_id)
        self.session.add(stats)
        await self.session.flush()
        return stats

    async def increment_likes(self, post_id: UUID, delta: int) -> None:
        stmt = (
            update(PostContentStats)
            .where(PostContentStats.post_id == post_id)
            .values(likes_count=func.greatest(PostContentStats.likes_count + delta, 0))
        )
        await self.session.execute(stmt)

    async def increment_comments(self, post_id: UUID, delta: int) -> None:
        stmt = (
            update(PostContentStats)
            .where(PostContentStats.post_id == post_id)
            .values(comments_count=func.greatest(PostContentStats.comments_count + delta, 0))
        )
        await self.session.execute(stmt)

    async def reset(self, post_id: UUID) -> None:
        stmt = (
            update(PostContentStats)
            .where(PostContentStats.post_id == post_id)
            .values(likes_count=0, comments_count=0)
        )
        await self.session.execute(stmt)
