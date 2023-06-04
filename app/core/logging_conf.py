import asyncio
import logging
import logging.config
import logging.handlers
from queue import SimpleQueue as Queue
from typing import List

from app.core.config import get_settings

settings = get_settings()

log_level = 'INFO' if not settings.DEBUG else 'DEBUG'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': log_level,
        'handlers': [
            'console',
        ],
    },
    'formatters': {
        'verbose': {'format': '[%(levelname)s] %(asctime)s %(module)s %(message)s'},
    },
    'handlers': {
        'console': {'level': log_level, 'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'loggers': {
        'charset_normalizer': {
            'level': 'INFO',
            'handlers': [],
            'propagate': False,
        },
    },
}


class LocalQueueHandler(logging.handlers.QueueHandler):
    def emit(self, record: logging.LogRecord) -> None:
        # Removed the call to self.prepare(), handle task cancellation
        try:
            self.enqueue(record)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f'LocalQueueHandler exception occurred: {e}')
            self.handleError(record)


def setup_logging_queue() -> None:
    """Move log handlers to a separate thread.

    Replace handlers on the root logger with a LocalQueueHandler,
    and start a logging.QueueListener holding the original
    handlers.

    """
    queue: Queue = Queue()
    root: logging.Logger = logging.getLogger()

    handlers: List[logging.Handler] = []

    handler: LocalQueueHandler = LocalQueueHandler(queue)
    root.addHandler(handler)
    for h in root.handlers[:]:
        if h is not handler:
            root.removeHandler(h)
            handlers.append(h)

    listener: logging.handlers.QueueListener = logging.handlers.QueueListener(
        queue, *handlers, respect_handler_level=True
    )
    listener.start()


logging.config.dictConfig(LOGGING)
setup_logging_queue()


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
