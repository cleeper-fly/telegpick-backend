import asyncio
import os
from typing import Any, Literal

from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.core.config import BASE_DIR, get_settings

__config_path__ = os.path.join(BASE_DIR, 'alembic.ini')
__migration_path__ = os.path.join(BASE_DIR, 'app', 'migrations')

cfg = Config(__config_path__)
cfg.set_main_option('script_location', __migration_path__)


async def migrate_db(conn_url: str, to: Literal['head', 'base'] = 'head') -> Any:
    async_engine = create_async_engine(conn_url)
    async with async_engine.begin() as conn:
        await conn.run_sync(_execute_upgrade, to)


def migrate_db_sync(conn_url: str, to: Literal['head', 'base'] = 'head', echo: bool = True) -> Any:
    engine: Engine = create_engine(conn_url, echo=echo)
    with engine.begin() as conn:
        _execute_upgrade(conn, to)


def _execute_upgrade(connection: AsyncConnection | Connection, to: Literal['head', 'base']) -> None:
    cfg.attributes['connection'] = connection
    if to == 'head':
        command.upgrade(cfg, to)
        return

    command.downgrade(cfg, to)


if __name__ == '__main__':
    settings = get_settings()
    asyncio.run(migrate_db(conn_url=settings.db_url))
