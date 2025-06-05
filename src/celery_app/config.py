from celery import Celery
from celery.schedules import crontab

from src.config.config import settings

if settings.DOCKER:
    broker_url = settings.get_rmq_url()
else:
    broker_url = "amqp://guest:guest@localhost:5672//"


celery_app = Celery(
    "src.celery_app.config",
    broker=broker_url,
)

celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True

celery_app.conf.beat_schedule = {
    "get_pets_for_reminders_every_morning": {
        "task": "src.celery_app.beat_schedule.get_pets_for_reminders",
        "schedule": crontab(hour=10, minute=0),
    },

    "get_pets_for_reminders_every_evening": {
        "task": "src.celery_app.beat_schedule.get_pets_for_reminders",
        "schedule": crontab(hour=20, minute=0),
    }
}
