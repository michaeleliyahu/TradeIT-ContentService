"""Event publisher for engagement events."""
import logging
from datetime import datetime
from uuid import UUID
from app.messaging.rabbitmq import rabbitmq_manager
from app.messaging.events import (
    PostLikedEvent,
    PostUnlikedEvent,
    PostCommentedEvent,
    CommentDeletedEvent,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publishes engagement events to RabbitMQ."""

    def __init__(self) -> None:
        self.manager = rabbitmq_manager

    def _routing(self, suffix: str) -> str:
        return f"{settings.content_routing_prefix}.{suffix}"

    async def publish_post_liked(self, post_id: UUID, user_id: UUID, occurred_at: datetime) -> None:
        event = PostLikedEvent(post_id=post_id, user_id=user_id, occurred_at=occurred_at)
        try:
            await self.manager.publish_event(event.model_dump(), self._routing("post.liked"))
        except Exception:  # noqa: BLE001
            logger.exception("Failed to publish PostLiked event")

    async def publish_post_unliked(self, post_id: UUID, user_id: UUID, occurred_at: datetime) -> None:
        event = PostUnlikedEvent(post_id=post_id, user_id=user_id, occurred_at=occurred_at)
        try:
            await self.manager.publish_event(event.model_dump(), self._routing("post.unliked"))
        except Exception:  # noqa: BLE001
            logger.exception("Failed to publish PostUnliked event")

    async def publish_post_commented(
        self, post_id: UUID, comment_id: UUID, user_id: UUID, content: str, occurred_at: datetime
    ) -> None:
        event = PostCommentedEvent(
            post_id=post_id,
            comment_id=comment_id,
            user_id=user_id,
            content=content,
            occurred_at=occurred_at,
        )
        try:
            await self.manager.publish_event(event.model_dump(), self._routing("post.commented"))
        except Exception:  # noqa: BLE001
            logger.exception("Failed to publish PostCommented event")

    async def publish_comment_deleted(
        self, post_id: UUID, comment_id: UUID, user_id: UUID, occurred_at: datetime
    ) -> None:
        event = CommentDeletedEvent(
            post_id=post_id,
            comment_id=comment_id,
            user_id=user_id,
            occurred_at=occurred_at,
        )
        try:
            await self.manager.publish_event(event.model_dump(), self._routing("comment.deleted"))
        except Exception:  # noqa: BLE001
            logger.exception("Failed to publish CommentDeleted event")


event_publisher = EventPublisher()


def get_event_publisher() -> EventPublisher:
    """Dependency provider for event publisher."""
    return event_publisher
