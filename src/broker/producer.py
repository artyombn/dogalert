import logging

from aio_pika import Message
from pydantic import ValidationError

from src.config.config import settings
from src.database.models import Notification as Notification_db
from src.schemas.notification import Notification

log = logging.getLogger(__name__)


async def send_task_to_rabbitmq(notification: Notification_db) -> None:
    settings.configure_logging()

    try:
        notification_pydantic = Notification.model_validate(notification, from_attributes=True)
        body = notification_pydantic.model_dump_json().encode('utf-8')
    except ValidationError as e:
        log.error(f"Pydantic validation error: {e}")
        return
    except Exception as e:
        log.error(f"Failed to get encoded body: {e}")
        raise

    try:
        connection = await settings.get_rmq_connection()
        async with connection:
            log.info(f"Created connection: {connection}")

            channel = await connection.channel()
            await channel.declare_queue(
                name=settings.RMQ_ROUTING_KEY,
                durable=True,
            )
            log.info(f"Declared queue: {settings.RMQ_ROUTING_KEY}")

            message = Message(
                body=body,
                delivery_mode=2,
            )

            await channel.default_exchange.publish(
                message=message,
                routing_key=settings.RMQ_ROUTING_KEY,
            )
            log.info(f"Successfully sent message to queue: {settings.RMQ_ROUTING_KEY}")

    except Exception as e:
        log.error(f"Failed to send message to rabbitmq: {e}")
        raise

