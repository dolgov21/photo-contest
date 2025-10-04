import typing
from datetime import datetime

from loguru import logger
from pydantic import ValidationError

from app.poller.schemas import (
    CallbackQuery,
    Chat,
    Message,
    InlineKeyboard,
    ReplyKeyboard,
    InlineKeyboardButton,
    Update,
    User,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


class UpdatesParser:
    def __init__(self, app: "Application"):
        self.app = app

    def _extract_chat(self, chat: dict) -> Chat:
        return Chat.model_validate(chat)

    def _extract_user(self, from_user: dict) -> User:
        return User.model_validate(from_user)

    def _extract_reply_markup(self, reply_markup: dict | None) -> InlineKeyboard | ReplyKeyboard | None:
        if reply_markup is None:
            return None

        if "inline_keyboard" in reply_markup:
            return InlineKeyboard.model_validate(reply_markup)

        if "keyboard" in reply_markup:
            return None

    def _extract_message(self, message: dict) -> Message:
        return Message(
            message_id=message["message_id"],
            from_user=self._extract_user(message["from"]),
            chat=self._extract_chat(message["chat"]),
            text=message.get("text"),
            reply_markup=self._extract_reply_markup(message.get("reply_markup")),
            date_time=datetime.fromtimestamp(message["date"]),
        )

    def _extract_callback_query(self, callback_query: dict) -> CallbackQuery:
        return CallbackQuery(
            id=callback_query["id"],
            from_user=self._extract_user(callback_query["from"]),
            message=self._extract_message(callback_query["message"]),
            data=callback_query["data"],
        )

    @logger.catch(ValidationError)
    def _create_update(self, update: dict) -> Update | None:
        message: dict = update.get("message")
        callback_query: dict = update.get("callback_query")

        if not (message or callback_query):
            return None

        update_object = Update(update_id=update["update_id"])

        if message is not None:
            update_object.message = self._extract_message(message)

        if callback_query is not None:
            update_object.callback_query = self._extract_callback_query(
                callback_query
            )

        return update_object

    def parse_data(self, data: dict):
        updates = data.get("result", [])
        logger.debug(f"Received updates: {updates}")

        for update in updates:
            try:
                update_object = self._create_update(update)
                logger.debug(f"Produced update: {update_object}")

                if update_object:
                    self.app.updates_queue.put_nowait(update_object)

                logger.debug(
                    f"Updates in queue: {self.app.updates_queue.qsize()}"
                )
            except Exception as e:
                logger.opt(exception=e).error(
                    f"Failed to parse, update_id: {update.get('update_id')}"
                )
