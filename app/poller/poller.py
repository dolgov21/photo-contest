import asyncio
import typing
from asyncio import Future, Task
from urllib.parse import urlencode, urljoin

from aiohttp import TCPConnector
from aiohttp.client import ClientSession, ClientTimeout
from pydantic import ValidationError
from loguru import logger

from app.base.base_service import BaseService
from app.poller.schemas import Update

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

    async def startup(self, app: "Application"):
        self.session = ClientSession(
            connector=TCPConnector(),
            timeout=ClientTimeout(total=app.config.bot.timeout + 5),
        )

        self.start()
        logger.info("UpdatesPoller running...")

    async def shutdown(self, app: "Application"):
        await self.stop()
        logger.info("UpdatesPoller stopped.")

    def _build_query(self, method: str, params: dict) -> str:
        base_url = urljoin(
            self.API_PATH, f"/bot{self.app.config.bot.token}/{method}"
        )
        return f"{base_url}?{urlencode(params)}"

    def _parse_updates(self, data: dict) -> list[Update]:
        updates = data.get("result", [])
        logger.debug(f"Received updates: {updates}")

        updates_obj = []
        for raw in updates:
            try:
                update = Update.model_validate(raw)
                updates_obj.append(update)
                logger.debug(f"Produced update: {update}")
            except ValidationError as e:
                logger.opt(exception=e).error(
                    f"Failed to parse, update_id: {raw.get('update_id')}"
                )
        return updates_obj

    def _add_queue_updates(self, updates: list[Update]):
        for update in updates:
            self.app.updates_queue.put_nowait(update)
            logger.debug(f"Updates in queue: {self.app.updates_queue.qsize()}")

    def _process_data(self, data: dict):
        """Возвращает True, если результат ожидаемый."""
        if not data.get("ok"):
            logger.error(f"Telegram API error: {data}")
            return False
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

                updates = self._parse_updates(data)
                self._add_queue_updates(updates)

                if updates:
                    self.last_update_id = max(
                        update.update_id for update in updates
                    )

    def _done_callback(self, result: Future) -> None:
        if result.exception():
            logger.opt(exception=result.exception()).error(
                "UpdatesPoller stopped with exception"
            )

        if self.is_running:
            self.start()

    def start(self):
        self.is_running = True
        self.poll_task = asyncio.create_task(self._loop_poll())
        self.poll_task.add_done_callback(self._done_callback)

    async def stop(self):
        self.is_running = False
        logger.info("Stopping telegram updates poller...")
        if self.poll_task:
            await self.poll_task
        await self.session.close()


def setup_poller(app: "Application"):
    app.poller = UpdatesPoller(app)
    app.updates_queue = asyncio.Queue()
