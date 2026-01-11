"""HTTP routes for likes, comments, and stats."""
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.messaging.publisher import EventPublisher, get_event_publisher
from app.services.engagement_service import EngagementService
from app.schemas.like import LikeResponse
from app.schemas.comment import CommentCreate, CommentResponse, CommentListResponse
from app.schemas.stats import PostStatsResponse

router = APIRouter(prefix="/posts", tags=["engagement"])


def get_engagement_service(
    db: AsyncSession = Depends(get_db),
    publisher: EventPublisher = Depends(get_event_publisher),
) -> EngagementService:
    return EngagementService.build(db, publisher)


@router.post("/{post_id}/like", response_model=LikeResponse, status_code=status.HTTP_201_CREATED)
async def like_post(
    post_id: UUID,
    current_user: UUID = Depends(get_current_user),
    service: EngagementService = Depends(get_engagement_service),
):
    """Like a post for the current user."""
    return await service.like_post(post_id, current_user)


@router.delete("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_post(
    post_id: UUID,
    current_user: UUID = Depends(get_current_user),
    service: EngagementService = Depends(get_engagement_service),
):
    """Remove a like from the current user."""
    await service.unlike_post(post_id, current_user)


@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_comment(
    post_id: UUID,
    payload: CommentCreate,
    current_user: UUID = Depends(get_current_user),
    service: EngagementService = Depends(get_engagement_service),
):
    """Add a comment to a post."""
    return await service.add_comment(post_id, current_user, payload.content)


@router.get("/{post_id}/comments", response_model=CommentListResponse)
async def list_comments(
    post_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        default=settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description="Items per page",
    ),
    service: EngagementService = Depends(get_engagement_service),
):
    """List comments for a post."""
    return await service.list_comments(post_id, page, page_size)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    current_user: UUID = Depends(get_current_user),
    service: EngagementService = Depends(get_engagement_service),
):
    """Soft delete a comment owned by the current user."""
    await service.delete_comment(comment_id, current_user)


@router.get("/{post_id}/stats", response_model=PostStatsResponse)
async def get_post_stats(
    post_id: UUID,
    service: EngagementService = Depends(get_engagement_service),
):
    """Fetch aggregated engagement stats for a post."""
    return await service.get_stats(post_id)
