import typing
from urllib.parse import urlencode, urljoin

from loguru import logger
from aiohttp import TCPConnector
from aiohttp.client import ClientSession, ClientTimeout

if typing.TYPE_CHECKING:
    from app.web.app import Application

class TgApiPoller:
    API_PATH = "https://api.telegram.org/"

    def __init__(self, app: "Application"):
        self.app = app

        self.last_update_id = 0
        self.polling = False
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False), timeout=ClientTimeout(total=30))

    def _build_query(self, method: str, params: dict) -> str:
        base_url = urljoin(self.API_PATH, f"/bot{self.app.config.bot.token}/{method}")
        return f"{base_url}?{urlencode(params)}"

    async def _loop_poll(self):
        while self.polling:
            async with self.session.get(
                self._build_query(
                    method="getUpdates",
                    params={
                        "timeout": 25,
                        "offset": self.last_update_id + 1
                    }
                )
            ) as response:
                data = await response.json()
                logger.debug(data)
                if data["result"]:
                    self.last_update_id = max(update["update_id"] for update in data["result"])

    async def start(self):
        self.polling = True
        logger.info("starting telegram poller...")
        await self._loop_poll()


def setup_poller(app: "Application"):
    app.poller = TgApiPoller(app)
