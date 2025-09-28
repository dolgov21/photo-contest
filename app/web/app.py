import asyncio
from typing import Any, Coroutine, Union

from loguru import logger

from app.config import Config, setup_config
from app.poller.poller import TgApiPoller, setup_poller
from app.store.store import Store, setup_store

__all__ = ("Application",)


class Application:
    config: Config
    store: Store
    poller: TgApiPoller

    ScraperHooks = Union[Coroutine[Any, Any, Any]]
    on_startup: list[ScraperHooks] = None
    on_shutdown: list[ScraperHooks] = None

    def __init__(self):
        self.on_startup = []
        self.on_shutdown = []

    async def _hooks_handler(self, hooks: list[ScraperHooks]):
        for hook in hooks:
            await hook()
            logger.debug(f"{hook} hook был отработан")

    async def setup(self):
        await self._hooks_handler(self.on_startup)

    async def close(self):
        await self._hooks_handler(self.on_shutdown)


app = Application()


async def _setup_app(config_path: str):
    setup_config(app, config_path)
    setup_store(app)
    setup_poller(app)
    logger.info("setup services")

    await app.setup()
    logger.info("setup hooks")


async def start_app(config_path: str):
    await _setup_app(config_path)

    poller = asyncio.create_task(app.poller.start())
    await poller
