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
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None


class Message(BaseModel):
    message_id: int
    from_user: User
    chat: Chat
    text: str | None
    date_time: datetime


class CallbackQuery(BaseModel):
    id: int
    from_user: User
    message: Message


class Update(BaseModel):
    update_id: int
    message: Message | None = None
    callback_query: CallbackQuery | None = None
