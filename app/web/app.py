import asyncio
import logging

from aiohttp.web import (
    Application as AiohttpApplication,
    Request as AiohttpRequest,
    View as AiohttpView,
    run_app,
)
from aiohttp_apispec import setup_aiohttp_apispec
from loguru import logger

from app.bot.updates_handler import UpdatesHandler, setup_handler
from app.config import Config, setup_config
from app.db.database import Database, setup_database
from app.db.models.admin import AdminModel
from app.poller.poller import UpdatesPoller, setup_poller
from app.store.store import Store, setup_store
from app.web.mw import setup_middlewares
from app.web.routes import setup_routes
from app.web.session import setup_session


class Application(AiohttpApplication):
    config: Config
    store: Store
    poller: UpdatesPoller
    handler: UpdatesHandler
    database: Database

    updates_queue: asyncio.Queue


class Request(AiohttpRequest):
    admin: AdminModel | None = None

    @property
    def app(self) -> Application:
        return super().app()


class View(AiohttpView):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def store(self) -> Store:
        return self.request.app.store

    @property
    def data(self) -> dict:
        return self.request.get("data", {})


app = Application()


def setup_logging():
    # Перенаправляем logging в loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            logger.opt(depth=6, exception=record.exc_info).log(
                level, record.getMessage()
            )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    logging.getLogger("aiohttp.access").setLevel(logging.INFO)
    logging.getLogger("aiohttp.server").setLevel(logging.INFO)
    logging.getLogger("aiohttp.web").setLevel(logging.INFO)
    logging.getLogger("aiohttp.internal").setLevel(logging.WARNING)


def setup_app(config_path: str) -> Application:
    setup_logging()

    setup_aiohttp_apispec(
        app=app,
        title="Admin API",
        version="1.0.0",
        url="/api/docs/swagger.json",
        swagger_path="/api/docs",
    )

    setup_config(app, config_path)
    setup_session(app)
    setup_middlewares(app)
    setup_database(app)
    setup_store(app)
    setup_poller(app)
    setup_handler(app)
    setup_routes(app)

    logger.info("Setup services")
    return app


def start_app(config_path: str):
    application = setup_app(config_path=config_path)

    run_app(
        application,
        host=application.config.web.host,
        port=application.config.web.port,
        print=application.config.web.print,
    )
