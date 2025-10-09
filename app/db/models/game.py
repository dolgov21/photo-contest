import typing

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base, TimestampMixin

if typing.TYPE_CHECKING:
    from app.db.models.users_chats import ChatModel, UserModel

__all__ = ("ContestModel", "MatchModel", "RoundModel", "VoteModel")


class ContestModel(Base, TimestampMixin):
    __tablename__ = "contests"

    contest_id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.chat_id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    chat: Mapped["ChatModel"] = relationship(
        "ChatModel", back_populates="contests"
    )
    rounds: Mapped[list["RoundModel"]] = relationship(
        "RoundModel", back_populates="contest", cascade="all, delete"
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

    votes: Mapped[list["VoteModel"]] = relationship(
        "VoteModel", back_populates="match", cascade="all, delete"
    )


class VoteModel(Base, TimestampMixin):
    __tablename__ = "votes"

    vote_id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.match_id", ondelete="CASCADE"), nullable=False
    )
    voter_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    voted_for_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )

    match: Mapped["MatchModel"] = relationship(
        "MatchModel", back_populates="votes"
    )
    voter: Mapped["UserModel"] = relationship(
        "UserModel", foreign_keys=[voter_id]
    )
    voted_for: Mapped["UserModel"] = relationship(
        "UserModel", foreign_keys=[voted_for_id]
    )
