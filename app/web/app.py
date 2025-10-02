import asyncio

from aiohttp.web import (
    Application as AiohttpApplication,
    run_app,
)
from loguru import logger

from app.bot.updates_handler import UpdatesHandler, setup_handler
from app.config import Config, setup_config
from app.poller.poller import UpdatesPoller, setup_poller
from app.store.store import Store, setup_store


class Application(AiohttpApplication):
    config: Config
    store: Store
    poller: UpdatesPoller
    handler: UpdatesHandler

    updates_queue: asyncio.Queue


app = Application()


def setup_app(config_path: str):
    setup_config(app, config_path)
    setup_store(app)
    setup_poller(app)
    setup_handler(app)

    logger.info("Setup services")
    return app


def start_app(config_path: str):
    run_app(setup_app(config_path=config_path), print=None)
