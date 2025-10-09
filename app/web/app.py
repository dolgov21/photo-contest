import asyncio
import logging

from aiohttp.web import (
    Application as AiohttpApplication,
    run_app,
)
from loguru import logger

from app.bot.updates_handler import UpdatesHandler, setup_handler
from app.config import Config, setup_config
from app.db.database import Database, setup_database
from app.poller.poller import UpdatesPoller, setup_poller
from app.store.store import Store, setup_store


class Application(AiohttpApplication):
    config: Config
    store: Store
    poller: UpdatesPoller
    handler: UpdatesHandler
    database: Database

    updates_queue: asyncio.Queue


app = Application()


def setup_logging():
    # Перенаправляем logging в loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    logging.getLogger("aiohttp.access").setLevel(logging.INFO)
    logging.getLogger("aiohttp.server").setLevel(logging.INFO)
    logging.getLogger("aiohttp.web").setLevel(logging.INFO)
    logging.getLogger("aiohttp.internal").setLevel(logging.WARNING)


def setup_app(config_path: str) -> Application:
    setup_logging()
    
    setup_config(app, config_path)
    setup_database(app)
    setup_store(app)
    setup_poller(app)
    setup_handler(app)

    logger.info("Setup services")
    return app


def start_app(config_path: str):
    run_app(setup_app(config_path=config_path), print=None)
