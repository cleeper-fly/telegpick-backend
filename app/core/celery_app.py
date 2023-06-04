from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery('worker', broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)

celery_app.conf.task_routes = {'app.apps.telegpick.tasks.*': 'main-queue'}

celery_app.conf.beat_schedule = {
    'process_all_pics_task': {
        'task': 'app.apps.telegpick.tasks.process_all_pics_task',
        'schedule': crontab(minute="*"),
    },
}

celery_app.conf.timezone = 'UTC'

celery_app.autodiscover_tasks(
    ['app.apps.telegpick.tasks'],
)
