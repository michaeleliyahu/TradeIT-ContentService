"""Business logic for likes, comments, and counters."""
import logging
from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.like_repository import LikeRepository
from app.repositories.comment_repository import CommentRepository
from app.repositories.stats_repository import StatsRepository
from app.messaging.publisher import EventPublisher
from app.schemas.comment import CommentListResponse

logger = logging.getLogger(__name__)


class EngagementService:
    """Encapsulates engagement workflows for posts."""

    def __init__(
        self,
        session: AsyncSession,
        like_repo: LikeRepository,
        comment_repo: CommentRepository,
        stats_repo: StatsRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self.session = session
        self.like_repo = like_repo
        self.comment_repo = comment_repo
        self.stats_repo = stats_repo
        self.event_publisher = event_publisher

    @classmethod
    def build(cls, session: AsyncSession, publisher: EventPublisher) -> "EngagementService":
        return cls(
            session=session,
            like_repo=LikeRepository(session),
            comment_repo=CommentRepository(session),
            stats_repo=StatsRepository(session),
            event_publisher=publisher,
        )

    async def like_post(self, post_id: UUID, user_id: UUID):
        await self.stats_repo.ensure_stats(post_id)
        existing = await self.like_repo.get_by_post_and_user(post_id, user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Post already liked by user",
            )
        try:
            like = await self.like_repo.create_like(post_id, user_id)
            await self.stats_repo.increment_likes(post_id, 1)
            await self.session.commit()
            await self.session.refresh(like)
            await self.event_publisher.publish_post_liked(
                post_id=post_id,
                user_id=user_id,
                occurred_at=like.created_at,
            )
            return like
        except Exception:  # noqa: BLE001
            await self.session.rollback()
            logger.exception("Failed to like post %s", post_id)
            raise

    async def unlike_post(self, post_id: UUID, user_id: UUID) -> None:
        await self.stats_repo.ensure_stats(post_id)
        like = await self.like_repo.get_by_post_and_user(post_id, user_id)
        if not like:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Like not found for user",
            )
        try:
            await self.like_repo.delete_like(like)
            await self.stats_repo.increment_likes(post_id, -1)
            await self.session.commit()
            occurred_at = datetime.now(timezone.utc)
            await self.event_publisher.publish_post_unliked(
                post_id=post_id,
                user_id=user_id,
                occurred_at=occurred_at,
            )
        except Exception:  # noqa: BLE001
            await self.session.rollback()
            logger.exception("Failed to unlike post %s", post_id)
            raise

    async def add_comment(self, post_id: UUID, user_id: UUID, content: str):
        await self.stats_repo.ensure_stats(post_id)
        try:
            comment = await self.comment_repo.create_comment(post_id, user_id, content)
            await self.stats_repo.increment_comments(post_id, 1)
            await self.session.commit()
            await self.session.refresh(comment)
            await self.event_publisher.publish_post_commented(
                post_id=post_id,
                comment_id=comment.id,
                user_id=user_id,
                content=comment.content,
                occurred_at=comment.created_at,
            )
            return comment
        except Exception:  # noqa: BLE001
            await self.session.rollback()
            logger.exception("Failed to add comment to post %s", post_id)
            raise

    async def list_comments(self, post_id: UUID, page: int, page_size: int) -> CommentListResponse:
        comments, total = await self.comment_repo.list_comments(post_id, page, page_size)
        has_next = (page * page_size) < total
        has_prev = page > 1
        return CommentListResponse(
            items=comments,
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_prev=has_prev,
        )

    async def delete_comment(self, comment_id: UUID, user_id: UUID) -> None:
        comment = await self.comment_repo.get_comment(comment_id)
        if not comment or comment.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found",
            )
        if comment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this comment",
            )
        try:
            await self.comment_repo.soft_delete(comment)
            await self.stats_repo.increment_comments(comment.post_id, -1)
            await self.session.commit()
            occurred_at = datetime.now(timezone.utc)
            await self.event_publisher.publish_comment_deleted(
                post_id=comment.post_id,
                comment_id=comment.id,
                user_id=user_id,
                occurred_at=occurred_at,
            )
        except Exception:  # noqa: BLE001
            await self.session.rollback()
            logger.exception("Failed to delete comment %s", comment_id)
            raise

    async def get_stats(self, post_id: UUID):
        stats = await self.stats_repo.ensure_stats(post_id)
        await self.session.commit()
        return stats

    async def handle_post_created(self, post_id: UUID) -> None:
        try:
            await self.stats_repo.ensure_stats(post_id)
            await self.session.commit()
        except Exception:  # noqa: BLE001
            await self.session.rollback()
            logger.exception("Failed to initialize stats for post %s", post_id)
            raise

    async def handle_post_deleted(self, post_id: UUID) -> None:
        try:
            await self.stats_repo.ensure_stats(post_id)
            await self.comment_repo.soft_delete_by_post(post_id)
            await self.like_repo.delete_by_post(post_id)
            await self.stats_repo.reset(post_id)
            await self.session.commit()
        except Exception:  # noqa: BLE001
            await self.session.rollback()
            logger.exception("Failed to handle post deletion for %s", post_id)
            raise
