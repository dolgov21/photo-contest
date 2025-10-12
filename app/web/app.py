import asyncio

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


def setup_app(config_path: str):
    logger.add(
        "logs/app.log",
        rotation="5MB",
        compression="zip",
        level="DEBUG",
        enqueue=True,
    )
    
    setup_config(app, config_path)
    setup_database(app)
    setup_store(app)
    setup_poller(app)
    setup_handler(app)

    logger.info("Setup services")
    return app


def start_app(config_path: str):
    run_app(setup_app(config_path=config_path), print=None)
