"""API router aggregator."""
from fastapi import APIRouter
from app.api.routers import engagement, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(engagement.router)
