from dataclasses import dataclass


@dataclass
class Message:
    pass


@dataclass
class CallbackQuery:
    pass


@dataclass
class Update:
    update_id: int
    payload: Message | CallbackQuery
