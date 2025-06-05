from .config import celery_app

from . import reminder_tasks
from . import beat_schedule

__all__ = ['celery_app']
