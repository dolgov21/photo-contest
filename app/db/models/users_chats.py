from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base, TimestampMixin

__all__ = ("ChatModel", "UserChatsModel", "UserModel")


class UserModel(Base, TimestampMixin):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=False
    )
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str | None] = mapped_column(nullable=True)
    username: Mapped[str | None] = mapped_column(nullable=True)
    photo_id: Mapped[str | None] = mapped_column(nullable=True)

    chats: Mapped[list["ChatModel"]] = relationship(
        "ChatModel",
        secondary="users_chats",
        back_populates="users",
    )


class ChatModel(Base, TimestampMixin):
    __tablename__ = "chats"

    chat_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False
    )
    title: Mapped[str | None] = mapped_column(nullable=True)
    username: Mapped[str | None] = mapped_column(nullable=True)

    users: Mapped[list[UserModel]] = relationship(
        "UserModel",
        secondary="users_chats",
        back_populates="chats",
    )


class UserChatsModel(Base, TimestampMixin):
    __tablename__ = "users_chats"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.chat_id", ondelete="CASCADE"), primary_key=True
    )

    user: Mapped[UserModel] = relationship("UserModel", backref="user_chats")
    chat: Mapped[ChatModel] = relationship("ChatModel", backref="chat_users")
