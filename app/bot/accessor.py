import json
import typing
from urllib.parse import urlencode, urljoin

from aiohttp import ClientSession, ClientTimeout, TCPConnector
from loguru import logger

from app.base.base_accessor import BaseAccessor
from app.poller.schemas import InlineKeyboard, ReplyKeyboard

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotAccessor(BaseAccessor):
    API_PATH = "https://api.telegram.org/"

    def __init__(self, app: "Application"):
        super().__init__(app)
        self.app = app
        self.session: ClientSession | None = None

    async def connect(self, app: "Application"):
        self.session = ClientSession(
            connector=TCPConnector(),
            timeout=ClientTimeout(total=app.config.bot.timeout + 5),
        )
        logger.info("BotAccessor running...")

    async def disconnect(self, app: "Application"):
        await self.session.close()
        logger.info("BotAccessor stopped.")

    # def _build_query(self, method: str, params: dict) -> str:
    #     base_url = urljoin(
    #         self.API_PATH, f"/bot{self.app.config.bot.token}/{method}"
    #     )
    #     return f"{base_url}?{urlencode(params)}"

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: InlineKeyboard | ReplyKeyboard = None,
    ) -> dict:
        params = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        if reply_markup is not None:
            params["reply_markup"] = json.dumps(
                reply_markup.model_dump(exclude_none=True)
            )

        async with self.session.post(
            url=f"{self.API_PATH}bot{self.app.config.bot.token}/sendMessage",
            json=params,
        ) as response:
            result = await response.json()
            logger.debug(f"Answer: {result}")
            return result

    async def edit_message_text(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: InlineKeyboard | ReplyKeyboard = None,
    ) -> dict:
        params = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        if reply_markup is not None:
            params["reply_markup"] = json.dumps(
                reply_markup.model_dump(exclude_none=True)
            )

        async with self.session.post(
            url=f"{self.API_PATH}bot{self.app.config.bot.token}/editMessageText",
            json=params,
        ) as response:
            result = await response.json()
            logger.debug(f"Answer: {result}")
            return result

    async def get_user_photos(): ...
