import asyncio
import typing
from asyncio import Future, Task
from urllib.parse import urlencode, urljoin

from aiohttp import TCPConnector
from aiohttp.client import ClientSession, ClientTimeout
from loguru import logger

if typing.TYPE_CHECKING:
    from app.web.app import Application


class UpdatesPoller:
    API_PATH = "https://api.telegram.org/"

    def __init__(self, app: "Application"):
        self.app = app

        self.last_update_id = 0
        self.is_running = False
        self.poll_task: Task | None = None
        self.session = ClientSession(
            connector=TCPConnector(verify_ssl=False),
            timeout=ClientTimeout(total=30),
        )

    def _build_query(self, method: str, params: dict) -> str:
        base_url = urljoin(
            self.API_PATH, f"/bot{self.app.config.bot.token}/{method}"
        )
        return f"{base_url}?{urlencode(params)}"

    async def _process_data(self, data: dict):
        logger.debug(data)
        
    async def _loop_poll(self):
        while self.is_running:
            async with self.session.get(
                self._build_query(
                    method="getUpdates",
                    params={"timeout": 25, "offset": self.last_update_id + 1},
                )
            ) as response:
                data = await response.json()
                self._process_data(data)
                if data["result"]:
                    self.last_update_id = max(
                        update["update_id"] for update in data["result"]
                    )

    def _done_callback(self, result: Future) -> None:
        if result.exception():
            logger.opt(exception=result.exception()).error(
                "poller stopped with exception"
            )

        if self.is_running:
            self.start()

    def start(self):
        self.is_running = True
        logger.info("starting telegram poller...")
        self.poll_task = asyncio.create_task(self._loop_poll())
        self.poll_task.add_done_callback(self._done_callback)

    async def stop(self):
        self.is_running = False
        logger.info("stopping telegram poller...")
        await self.poll_task
        await self.session.close()


def setup_poller(app: "Application"):
    app.poller = UpdatesPoller(app)
