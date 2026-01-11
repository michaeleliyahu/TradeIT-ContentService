"""Main FastAPI application for Content Service."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import api_router
from app.core.config import settings
from app.db.database import async_session
from app.messaging.rabbitmq import rabbitmq_manager
from app.messaging.publisher import event_publisher
from app.messaging.events import PostCreatedEvent, PostDeletedEvent
from app.services.engagement_service import EngagementService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def _handle_post_event(routing_key: str, payload: dict) -> None:
    """Dispatch post lifecycle events to handlers."""
    async with async_session() as session:
        service = EngagementService.build(session, event_publisher)
        if routing_key == settings.post_created_routing_key:
            event = PostCreatedEvent(**payload)
            await service.handle_post_created(event.post_id)
        elif routing_key == settings.post_deleted_routing_key:
            event = PostDeletedEvent(**payload)
            await service.handle_post_deleted(event.post_id)
        else:
            logger.warning("Unhandled routing key: %s", routing_key)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown hooks."""
    logger.info("Starting Content Service...")
    try:
        await rabbitmq_manager.connect_with_retry()
        await rabbitmq_manager.start_post_consumer(_handle_post_event)
        logger.info("RabbitMQ consumer started")
    except Exception:  # noqa: BLE001
        logger.exception("RabbitMQ startup failed; continuing without consumer")
    yield
    logger.info("Shutting down Content Service...")
    try:
        await rabbitmq_manager.disconnect()
    except Exception:  # noqa: BLE001
        logger.exception("Error during RabbitMQ shutdown")


app = FastAPI(
    title=settings.service_name,
    version=settings.service_version,
    description="Content Service - Likes, comments, and engagement counters",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint with service metadata."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "status": "running",
    }
