"""Health check endpoints."""
from fastapi import APIRouter, Depends
from app.messaging.rabbitmq import RabbitMQManager, get_rabbitmq_manager
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """Return basic health info."""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.service_version,
    }


@router.get("/detailed")
async def detailed_health_check(
    rabbitmq: RabbitMQManager = Depends(get_rabbitmq_manager),
):
    """Return dependency-aware health info."""
    rabbit_ok = await rabbitmq.health_check()
    return {
        "status": "healthy" if rabbit_ok else "degraded",
        "service": settings.service_name,
        "version": settings.service_version,
        "dependencies": {"rabbitmq": "healthy" if rabbit_ok else "unhealthy"},
    }
