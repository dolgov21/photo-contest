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


class ReplyKeyboard(BaseModel): ...


class PhotoSize(BaseModel):
    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: int | None = None


class UserProfilePhotos(BaseModel):
    total_count: int
    photos: list[list[PhotoSize]]


class ReplyParameters(BaseModel):
    message_id: int


class Message(BaseModel):
    message_id: int
    from_user: User = Field(alias="from")
    chat: Chat
    text: str | None = None
    date_time: datetime = Field(alias="date")
    reply_markup: ReplyKeyboard | InlineKeyboard | None = None
    reply_parametrs: ReplyParameters | None = None
    photo: list[PhotoSize] | None = None
    caption: str | None = None
    media_group_id: str | None = None


class InputMediaPhoto(BaseModel):
    media: str
    type: str = "photo"
    caption: str | None = None


class SendMediaGroupResponse(BaseModel):
    ok: bool
    result: list[Message]

    @classmethod
    def model_validate(cls, obj: dict) -> "SendMediaGroupResponse":
        if isinstance(obj, list):
            return cls(ok=True, result=obj)
        return super().model_validate(obj)


class CallbackQuery(BaseModel):
    id: int
    from_user: User = Field(alias="from")
    message: Message
    data: str


class Update(BaseModel):
    update_id: int
    message: Message | None = None
    callback_query: CallbackQuery | None = None
