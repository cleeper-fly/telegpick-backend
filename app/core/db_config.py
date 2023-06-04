import importlib

from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker

from app.core.config import get_settings
from app.core.logging_conf import get_logger

settings = get_settings()
logger = get_logger(__name__)


engine = create_async_engine(settings.db_url, poolclass=NullPool)
# noinspection PyTypeChecker
AsyncSessionMaker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    future=True,
)


def get_app_models_path(app: str) -> str | None:
    app_models_path = f'{app}.models'
    try:
        importlib.import_module(app_models_path)
    except ImportError as e:
        if str(e) == f'No module named \'{app_models_path}\'':
            return None
        raise
    return app_models_path


def get_models() -> list[str]:
    models = []

    for app in settings.get_apps_list():
        if models_path := get_app_models_path(app):
            models.append(models_path)

    return models
