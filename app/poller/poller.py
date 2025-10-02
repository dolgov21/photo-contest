import asyncio
import typing
from asyncio import Future, Task
from urllib.parse import urlencode, urljoin

from aiohttp import TCPConnector
from aiohttp.client import ClientSession, ClientTimeout
from loguru import logger

from app.base.base_service import BaseService
from app.poller.parser import UpdatesParser

if typing.TYPE_CHECKING:
    from app.web.app import Application


class UpdatesPoller(BaseService):
    API_PATH = "https://api.telegram.org/"

    def __init__(self, app: "Application"):
        super().__init__(app)
        self.app = app

        self.last_update_id = 0
        self.is_running = False
        self.poll_task: Task | None = None
        self.session: ClientSession | None = None
        self.parser: UpdatesParser | None = None

    async def startup(self, app: "Application"):
        self.parser = UpdatesParser(app)
        self.session = ClientSession(
            connector=TCPConnector(),
            timeout=ClientTimeout(total=app.config.bot.timeout + 5),
        )

        self.start()
        logger.info("Poller running...")

    async def shutdown(self, app: "Application"):
        await self.stop()
        logger.info("Poller stopped.")

    def _build_query(self, method: str, params: dict) -> str:
        base_url = urljoin(
            self.API_PATH, f"/bot{self.app.config.bot.token}/{method}"
        )
        return f"{base_url}?{urlencode(params)}"

    def _process_data(self, data: dict):
        """Если результат ожидаемый,
        отправляет data на десериализацию в UpdatesParser и возвращает True.
        """
        if not data.get("ok"):
            logger.error(f"Telegram API error: {data}")
            return False

        self.parser.parse_data(data)
        return True

    async def _loop_poll(self):
        while self.is_running:
            async with self.session.get(
                self._build_query(
                    method="getUpdates",
                    params={
                        "timeout": self.app.config.bot.timeout,
                        "offset": self.last_update_id + 1,
                    },
                )
            ) as response:
                data = await response.json()
                if not self._process_data(data):
                    continue

                if data["result"]:
                    self.last_update_id = max(
                        update["update_id"] for update in data["result"]
                    )

    def _done_callback(self, result: Future) -> None:
        if result.exception():
            logger.opt(exception=result.exception()).error(
                "Poller stopped with exception"
            )

        if self.is_running:
            self.start()

    def start(self):
        self.is_running = True
        self.poll_task = asyncio.create_task(self._loop_poll())
        self.poll_task.add_done_callback(self._done_callback)

    async def stop(self):
        self.is_running = False
        logger.info("Stopping telegram poller...")
        await self.poll_task
        await self.session.close()


def setup_poller(app: "Application"):
    app.poller = UpdatesPoller(app)
    app.updates_queue = asyncio.Queue()
