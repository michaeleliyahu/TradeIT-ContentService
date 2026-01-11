"""Configuration management for Content Service."""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/content_db",
        description="PostgreSQL connection string",
    )

    # Service Configuration
    service_name: str = "Content Service"
    service_version: str = "1.0.0"
    debug: bool = False

    # RabbitMQ Configuration
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    post_exchange: str = "post_events"
    post_queue: str = "content_post_events"
    post_created_routing_key: str = "post.created"
    post_deleted_routing_key: str = "post.deleted"

    content_exchange: str = "content_events"
    content_routing_prefix: str = "content"

    # JWT Configuration for authentication
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"

    # Pagination defaults
    default_page_size: int = 20
    max_page_size: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
