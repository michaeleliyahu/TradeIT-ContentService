"""Repository for comment persistence operations."""
from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.comment import Comment


class CommentRepository:
    """Data access for comments."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_comment(self, post_id: UUID, user_id: UUID, content: str) -> Comment:
        comment = Comment(post_id=post_id, user_id=user_id, content=content)
        self.session.add(comment)
        await self.session.flush()
        return comment

    async def get_comment(self, comment_id: UUID) -> Optional[Comment]:
        stmt = select(Comment).where(Comment.id == comment_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_comments(
        self, post_id: UUID, page: int, page_size: int
    ) -> tuple[Sequence[Comment], int]:
        offset = (page - 1) * page_size
        base_query = select(Comment).where(Comment.post_id == post_id, Comment.is_deleted.is_(False))
        items_result = await self.session.execute(
            base_query.order_by(Comment.created_at.asc()).offset(offset).limit(page_size)
        )
        count_result = await self.session.execute(
            select(func.count()).where(
                Comment.post_id == post_id,
                Comment.is_deleted.is_(False),
            )
        )
        total = count_result.scalar_one()
        return items_result.scalars().all(), total

    async def soft_delete(self, comment: Comment) -> None:
        stmt = (
            update(Comment)
            .where(Comment.id == comment.id)
            .values(is_deleted=True)
        )
        await self.session.execute(stmt)

    async def soft_delete_by_post(self, post_id: UUID) -> None:
        stmt = update(Comment).where(Comment.post_id == post_id).values(is_deleted=True)
        await self.session.execute(stmt)
