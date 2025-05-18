import logging
from typing import TYPE_CHECKING

from src.config.config import settings

if TYPE_CHECKING:
    from pika.adapters.blocking_connection import BlockingChannel
    from pika.spec import Basic, BasicProperties

log = logging.getLogger(__name__)

def process_new_message(
        ch: "BlockingChannel",
        method: "Basic.Deliver",
        properties: "BasicProperties",
        body: bytes,
) -> None:
    log.info("ch: %s", ch)
    log.info("method: %s", method)
    log.info("properties: %s", properties)
    log.info("body: %s", body)

    log.warning("Finished processing message %s", body)

    ch.basic_ack(delivery_tag=method.delivery_tag)  # type: ignore[arg-type]

def main() -> None:
    settings.configure_logging()
    with settings.get_rmq_connection() as connection:
        log.info("Created connection: %s", connection)
        with connection.channel() as channel:
            log.info("Created channel: %s", channel)
            channel.queue_declare(queue=settings.RMQ_ROUTING_KEY)
            log.info("Queue declared: %r", settings.RMQ_ROUTING_KEY)
            channel.basic_consume(
                queue=settings.RMQ_ROUTING_KEY,
                on_message_callback=process_new_message,
            )
            log.info("WAITING for messages")
            channel.start_consuming()


if __name__ == "__main__":
    main()
