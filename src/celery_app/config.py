from celery import Celery

app = Celery(
    "src.celery_app.config",
    # broker=settings.get_rmq_url(),
    broker="amqp://guest:guest@localhost:5672//",
    backend='rpc://'
)
