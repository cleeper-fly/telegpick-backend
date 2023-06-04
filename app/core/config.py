from functools import lru_cache
from pathlib import Path

from pydantic import BaseSettings, SecretStr

PROJECT_ROOT = Path(__file__).parent.parent
BASE_DIR = PROJECT_ROOT.parent

ONE_SECOND = 1
ONE_MINUTE = ONE_SECOND * 60
ONE_HOUR = ONE_MINUTE * 60
ONE_DAY = ONE_HOUR * 24
ONE_MONTH: int = ONE_DAY * 30


class AppSettings(BaseSettings):
    """Service settings"""

    class Config(object):
        env_file = BASE_DIR.joinpath('.env')
        env_file_encoding = 'utf-8'
        use_enum_values = True

    # App
    APP_NAME: str = 'telegpick-backend'
    SECRET_KEY: SecretStr
    ALGORITHM: str = 'HS256'
    EXPIRATION_MINUTES: int = ONE_MONTH

    # Debug
    DEBUG: bool = False
    IS_TEST: bool = False

    # API
    API_PREFIX: str = '/api'
    AUTO_RELOAD: bool = False
    HOST: str = '127.0.0.1'
    PORT: int = 8000
    WEB_CONCURRENCY: int = 10

    # DB
    MAX_DB_CONNECTIONS = 100
    DB_HOST: str
    DB_USER: str
    DB_PASSWORD: SecretStr
    DB_NAME: str
    DB_PORT: int

    # telegram
    TELEGRAM_API_ID: int = 123123
    TELEGRAM_API_HASH: str = 'test'
    PICS_DIRECTORY: str = '/pics'
    SESSIONS_DIRECTORY: str = '/opt/sessions'

    # Celery
    CELERY_BROKER_URL: str = 'test'
    CELERY_RESULT_BACKEND: str = 'test'

    # Apps
    APPLICATIONS_MODULE: str = 'app.apps'
    APPLICATIONS: tuple[str, ...] = (
        'users',
        'telegpick',
    )

    def get_apps_list(self) -> tuple[str, ...]:
        return tuple(f'{self.APPLICATIONS_MODULE}.{app}' for app in self.APPLICATIONS)

    @property
    def db_url(self) -> str:
        return (
            f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD.get_secret_value()}'
            f'@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
        )


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
