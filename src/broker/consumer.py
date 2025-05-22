import asyncio
import json
import logging
from aio_pika import IncomingMessage
from pydantic import ValidationError

from src.bot.handlers.notification import send_notification_to_user
from src.config.config import settings
from src.schemas.notification import NotificationWithUrl

log = logging.getLogger(__name__)


async def process_new_message(message: IncomingMessage) -> None:
    log.info(f"Received message: {message.body}")

    try:
        data = json.loads(message.body.decode('utf-8'))
        notification = NotificationWithUrl(**data)
        log.info(f"Parsed notification: {notification}")

        for tg_id in notification.recipient_ids:
            await send_notification_to_user(tg_id, notification.message, notification.url)
            log.info(f"Sent notification to user {tg_id}")

        # async with asyncio.TaskGroup() as tg:
        #     [tg.create_task(
        #         send_notification_to_user(tg_id, notification.message)
        #     ) for tg_id in notification.recipient_ids]


        await message.ack()

    except json.JSONDecodeError as e:
        log.error(f"Failed to decode JSON: {e}")
        await message.nack(requeue=False)  # remove from queue
    except ValidationError as e:
        log.error(f"Pydantic validation failed: {e}")
        await message.nack(requeue=False)  # remove from queue
    except Exception as e:
        log.error(f"Failed to process notification: {e}")
        await message.nack(requeue=True)  # return to queue


async def handle_notification_from_rabbitmq() -> None:
    settings.configure_logging()
    log.info("Starting rabbitmq consumer...")

    try:
        connection = await settings.get_rmq_connection()
        async with connection:
            log.info("Created connection: %s", connection)

            channel = await connection.channel()
            await channel.set_qos(prefetch_count=10)

            queue = await channel.declare_queue(
                name=settings.RMQ_ROUTING_KEY,
                durable=True,
            )

            log.info("Waiting for messages in queue: %r", settings.RMQ_ROUTING_KEY)
            await queue.consume(process_new_message)

            while True:
                await asyncio.sleep(1)

    except Exception as e:
        log.error(f"Failed to fetch messages from rabbitmq: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(handle_notification_from_rabbitmq())
