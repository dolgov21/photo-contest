import typing

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base, TimestampMixin

if typing.TYPE_CHECKING:
    from app.db.models.users_chats import ChatModel, UserModel

__all__ = ("ContestModel", "MatchModel", "RoundModel")


class ContestModel(Base, TimestampMixin):
    __tablename__ = "contests"

    contest_id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.chat_id", ondelete="CASCADE"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True)
 
    chat: Mapped["ChatModel"] = relationship(
        "ChatModel", back_populates="contests"
    )
    rounds: Mapped[list["RoundModel"]] = relationship(
        "RoundModel", back_populates="contest", cascade="all, delete"
    )
    contests: Mapped[list["ContestModel"]] = relationship(
        "ContestModel",
        secondary="contest_participants",
        back_populates="participants",
    )


class RoundModel(Base, TimestampMixin):
    __tablename__ = "rounds"

    round_id: Mapped[int] = mapped_column(primary_key=True)
    contest_id: Mapped[int] = mapped_column(
        ForeignKey("contests.contest_id", ondelete="CASCADE"), nullable=False
    )
    round_number: Mapped[int] = mapped_column(nullable=False)
    is_finished: Mapped[bool] = mapped_column(default=False)

    contest: Mapped["ContestModel"] = relationship(
        "ContestModel", back_populates="rounds"
    )
    matches: Mapped[list["MatchModel"]] = relationship(
        "MatchModel", back_populates="round", cascade="all, delete"
    )


class MatchModel(Base, TimestampMixin):
    __tablename__ = "matches"

    match_id: Mapped[int] = mapped_column(primary_key=True)
    round_id: Mapped[int] = mapped_column(
        ForeignKey("rounds.round_id", ondelete="CASCADE"), nullable=False
    )

    user1_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    user2_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    votes_user1: Mapped[int] = mapped_column(default=0, nullable=False)
    votes_user2: Mapped[int] = mapped_column(default=0, nullable=False)
    winner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )

    round: Mapped["RoundModel"] = relationship(
        "RoundModel", back_populates="matches"
    )
    user1: Mapped["UserModel"] = relationship(
        "UserModel", foreign_keys=[user1_id]
    )
    user2: Mapped["UserModel"] = relationship(
        "UserModel", foreign_keys=[user2_id]
    )
    winner: Mapped["UserModel"] = relationship(
        "UserModel", foreign_keys=[winner_id]
    )
