"""RabbitMQ connection management and consumers/publishers."""
import asyncio
import json
import logging
from typing import Awaitable, Callable, Dict, Any, Optional
from aio_pika import Message, ExchangeType, connect_robust
from aio_pika.exceptions import AMQPConnectionError
from aio_pika.abc import (
    AbstractConnection,
    AbstractChannel,
    AbstractExchange,
    AbstractQueue,
)
from app.core.config import settings

logger = logging.getLogger(__name__)
EventHandler = Callable[[str, Dict[str, Any]], Awaitable[None]]


class RabbitMQManager:
    """Manages RabbitMQ connections, exchanges, and consumers."""

    def __init__(self) -> None:
        self.connection: Optional[AbstractConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self.post_exchange: Optional[AbstractExchange] = None
        self.content_exchange: Optional[AbstractExchange] = None
        self._consumer_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """Establish connection and declare exchanges."""
        self.connection = await connect_robust(settings.rabbitmq_url, loop=asyncio.get_event_loop())
        self.channel = await self.connection.channel()

        self.post_exchange = await self.channel.declare_exchange(
            settings.post_exchange,
            ExchangeType.TOPIC,
            durable=True,
        )
        self.content_exchange = await self.channel.declare_exchange(
            settings.content_exchange,
            ExchangeType.TOPIC,
            durable=True,
        )
        logger.info("RabbitMQ connected")

    async def connect_with_retry(self, retries: int = 5, delay: float = 5.0) -> None:
        """Attempt to connect with retries when broker is not ready."""
        for attempt in range(retries):
            try:
                await self.connect()
                return
            except AMQPConnectionError:
                logger.warning(
                    "RabbitMQ not ready, retrying in %ss... (%s/%s)", delay, attempt + 1, retries
                )
                await asyncio.sleep(delay)
        raise RuntimeError("Failed to connect to RabbitMQ after retries")

    async def disconnect(self) -> None:
        """Close consumer and connection."""
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
            self._consumer_task = None

        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("RabbitMQ disconnected")

    async def publish_event(self, event_data: Dict[str, Any], routing_key: str) -> None:
        """Publish event to the content exchange."""
        if not self.content_exchange:
            raise RuntimeError("RabbitMQ is not connected")

        message_body = json.dumps(event_data, default=str)
        message = Message(
            message_body.encode(),
            content_type="application/json",
            delivery_mode=2,
        )
        await self.content_exchange.publish(message, routing_key=routing_key)

    async def start_post_consumer(self, handler: EventHandler) -> None:
        """Start consumer for post lifecycle events."""
        if not self.channel or not self.post_exchange:
            raise RuntimeError("RabbitMQ channel not ready")

        queue: AbstractQueue = await self.channel.declare_queue(
            settings.post_queue,
            durable=True,
        )
        await queue.bind(self.post_exchange, routing_key=settings.post_created_routing_key)
        await queue.bind(self.post_exchange, routing_key=settings.post_deleted_routing_key)

        async def _consume() -> None:
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            payload = json.loads(message.body)
                            await handler(message.routing_key, payload)
                        except Exception as exc:  # noqa: BLE001
                            logger.exception("Failed to process post event: %s", exc)

        self._consumer_task = asyncio.create_task(_consume())

    async def health_check(self) -> bool:
        """Return connection health status."""
        return (
            self.connection is not None
            and not self.connection.is_closed
            and self.channel is not None
            and not self.channel.is_closed
        )


rabbitmq_manager = RabbitMQManager()


async def get_rabbitmq_manager() -> RabbitMQManager:
    """Dependency provider for RabbitMQ manager."""
    return rabbitmq_manager
