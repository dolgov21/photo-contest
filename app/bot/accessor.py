import functools
import json
import typing
from typing import TypeVar

from aiohttp import ClientSession, ClientTimeout, TCPConnector
from loguru import logger
from pydantic import ValidationError

from app.base.base_accessor import BaseAccessor
from app.poller.schemes import (
    InlineKeyboard,
    InputMediaPhoto,
    Message,
    ReplyKeyboard,
    ReplyParameters,
    SendMediaGroupResponse,
    UserProfilePhotos,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application

T = TypeVar("T")


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

    @staticmethod
    def api_request(expected_model: None | type[T] = None):
        def wrapper(func):
            @functools.wraps(func)
            async def inner(self, *args, **kwargs):
                resp = await func(self, *args, **kwargs)
                logger.debug(f"Raw data: {resp}")

                if expected_model and isinstance(resp, dict):
                    result = resp.get("result")
                    try:
                        result_obj = expected_model.model_validate(result)
                        logger.debug(f"Validated response: {result_obj}")
                    except ValidationError as e:
                        logger.opt(exception=e).error("Validation error")
                        return resp
                    else:
                        return result_obj
                return resp

            return inner

        return wrapper

    @api_request(expected_model=Message)
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: InlineKeyboard | ReplyKeyboard = None,
        reply_parameters: ReplyParameters = None,
    ) -> Message:
        params = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        if reply_markup is not None:
            params["reply_markup"] = json.dumps(
                reply_markup.model_dump(exclude_none=True)
            )

        if reply_parameters is not None:
            params["reply_parameters"] = json.dumps(
                reply_parameters.model_dump(exclude_none=True)
            )

        async with self.session.post(
            url=f"{self.API_PATH}bot{self.app.config.bot.token}/sendMessage",
            json=params,
        ) as response:
            return await response.json()

    @api_request(expected_model=Message)
    async def edit_message_text(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: InlineKeyboard | ReplyKeyboard = None,
    ) -> Message:
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
            return await response.json()

    @api_request(expected_model=UserProfilePhotos)
    async def get_user_profile_photos(
        self,
        user_id: int,
        limit: int = 1,
    ) -> UserProfilePhotos:
        params = {
            "user_id": user_id,
            "limit": limit,
        }

        async with self.session.post(
            url=f"{self.API_PATH}bot{self.app.config.bot.token}/getUserProfilePhotos",
            json=params,
        ) as response:
            return await response.json()

    @api_request()
    async def answer_callback_query(
        self, callback_query_id: int, text: str, show_alert: bool = False
    ) -> dict:
        params = {
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": show_alert,
        }

        async with self.session.post(
            url=f"{self.API_PATH}bot{self.app.config.bot.token}/answerCallbackQuery",
            json=params,
        ) as response:
            return await response.json()

    @api_request(expected_model=Message)
    async def edit_message_reply_markup(
        self,
        chat_id: int,
        message_id: int,
        reply_markup: InlineKeyboard | None = None,
    ) -> Message:
        params = {
            "chat_id": chat_id,
            "message_id": message_id,
        }

        if reply_markup is not None:
            params["reply_markup"] = json.dumps(
                reply_markup.model_dump(exclude_none=True)
            )

        async with self.session.post(
            url=f"{self.API_PATH}bot{self.app.config.bot.token}/editMessageReplyMarkup",
            json=params,
        ) as response:
            return await response.json()

    @api_request(expected_model=SendMediaGroupResponse)
    async def send_media_group(
        self,
        chat_id: int,
        media: list[InputMediaPhoto],
    ) -> SendMediaGroupResponse:
        media_data = [item.model_dump(exclude_none=True) for item in media]

        params = {
            "chat_id": chat_id,
            "media": media_data,
        }

        async with self.session.post(
            url=f"{self.API_PATH}bot{self.app.config.bot.token}/sendMediaGroup",
            json=params,
        ) as response:
            return await response.json()

    async def send_media_group_with_keyboard(
        self,
        chat_id: int,
        media: list[InputMediaPhoto],
        question_text: str,
        reply_markup: InlineKeyboard,
    ) -> Message:
        try:
            media_group_response = await self.send_media_group(chat_id, media)

            if not media_group_response or not media_group_response.ok:
                logger.error("Failed to send media group")
                return await self.send_message(
                    chat_id=chat_id,
                    text=question_text,
                    reply_markup=reply_markup,
                )

            question_message = await self.send_message(
                chat_id=chat_id, text=question_text, reply_markup=reply_markup
            )

            logger.info(
                f"Question message sent with ID: {question_message.message_id}"
            )

        except Exception as e:
            logger.opt(exception=e).error(
                "Error in send_media_group_with_keyboard"
            )
            return await self.send_message(
                chat_id=chat_id, text=question_text, reply_markup=reply_markup
            )
        else:
            return question_message
