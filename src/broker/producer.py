import logging

from src.config.config import settings

log = logging.getLogger(__name__)

def main() -> None:
    settings.configure_logging()
    with settings.get_rmq_connection() as connection:
        log.info("Created connection: %s", connection)
        with connection.channel() as channel:
            log.info("Created channel: %s", channel)
            channel.queue_declare(queue=settings.RMQ_ROUTING_KEY)
            log.info("Queue declared: %r", settings.RMQ_ROUTING_KEY)
            channel.basic_publish(
                exchange=settings.RMQ_EXCHANGE,
                routing_key=settings.RMQ_ROUTING_KEY,
                body="Hello WWWorld!",  # type: ignore[arg-type]
            )

            while True:
                pass

if __name__ == "__main__":
    main()
