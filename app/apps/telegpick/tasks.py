import asyncio
import threading
from datetime import datetime

import pytz
from asgiref.sync import async_to_sync

from app.apps.telegpick.use_cases import ProcessPicsTaskUseCase
from app.core.celery_app import celery_app

celery_app.loop = asyncio.new_event_loop()
celery_app.loop_runner = threading.Thread(
    target=celery_app.loop.run_forever,
    daemon=True,
)
celery_app.loop_runner.start()


@celery_app.task()
def process_all_pics_task():
    current_time = datetime.now(pytz.utc)
    async_to_sync(ProcessPicsTaskUseCase(current_time).execute)()
    return
