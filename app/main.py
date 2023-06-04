import asyncio

import uvicorn
from fastapi import FastAPI

from app.core.config import get_settings
from app.core.init_app import init_middlewares, register_events, register_routers
from app.core.logging_conf import get_logger

config = get_settings()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    logger.info('Initializing app...')
    app = FastAPI(title=config.APP_NAME)
    init_middlewares(app)
    register_routers(app)
    register_events(app)
    logger.info('Done!')
    return app


if __name__ == '__main__':
    # # https://art049.github.io/odmantic/usage_fastapi/#building-the-engine
    _config = uvicorn.Config(
        app='main:create_app',
        factory=True,
        host=config.HOST,
        port=config.PORT,
        reload=config.AUTO_RELOAD,
        workers=config.WEB_CONCURRENCY,
    )
    server = uvicorn.Server(_config)
    asyncio.run(server.serve())
