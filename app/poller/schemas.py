from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ChatTypes(StrEnum):
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"


class Chat(BaseModel):
    id: int
    title: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    chat_type: ChatTypes = Field(alias="type")


class User(BaseModel):
    id: int
    is_bot: bool
    first_name: str
    last_name: str | None = None
    username: str | None = None


class InlineKeyboardButton(BaseModel):
    text: str
    callback_data: str | None = None
    url: str | None = None


class InlineKeyboard(BaseModel):
    inline_keyboard: list[list[InlineKeyboardButton]]


class ReplyKeyboard(BaseModel):
    ...


class PhotoSize(BaseModel):
    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: int | None = None


class Message(BaseModel):
    message_id: int
    from_user: User = Field(alias="from")
    chat: Chat
    text: str | None
    date_time: datetime = Field(alias="date")
    reply_markup: ReplyKeyboard | InlineKeyboard | None = None
    photo: list[PhotoSize] | None = None


class CallbackQuery(BaseModel):
    id: int
    from_user: User = Field(alias="from")
    message: Message
    data: str


class Update(BaseModel):
    update_id: int
    message: Message | None = None
    callback_query: CallbackQuery | None = None
