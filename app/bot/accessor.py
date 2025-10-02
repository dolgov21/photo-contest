import typing
from urllib.parse import urlencode, urljoin

from aiohttp import ClientSession, ClientTimeout, TCPConnector
from loguru import logger

from app.base.base_accessor import BaseAccessor

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotAccessor(BaseAccessor):
    API_PATH = "https://api.telegram.org/"

    def __init__(self, app: "Application"):
        super().__init__(app)
        self.app = app
        logger.debug("BotAccessor initialized")
        self.session: ClientSession | None = None

    async def connect(self, app: "Application"):
        self.session = ClientSession(
            connector=TCPConnector(),
            timeout=ClientTimeout(total=app.config.bot.timeout + 5),
        )
        logger.info("UpdatesHandler running...")

    async def disconnect(self, app: "Application"):
        await self.session.close()
        logger.info("UpdatesHandler stopped.")

    def _build_query(self, method: str, params: dict) -> str:
        base_url = urljoin(
            self.API_PATH, f"/bot{self.app.config.bot.token}/{method}"
        )
        logger.debug(f"{base_url}?{urlencode(params)}")
        return f"{base_url}?{urlencode(params)}"

    async def send_message(self, chat_id: int, text: str):
        logger.debug("enter to the send_message")
        async with self.session.get(
            self._build_query(
                "sendMessage",
                params={"chat_id": chat_id, "text": text},
            )
        ) as response:
            data = await response.json()
            logger.debug(data)
