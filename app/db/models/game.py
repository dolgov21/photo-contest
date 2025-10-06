from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base, TimestampMixin

__all__ = (
    "ContestModel",
    "MatchModel",
    "RoundModel",
    "ChatModel",
    "UserModel",
    "ContestsParticipantsModel",
)


class ContestsParticipantsModel(Base, TimestampMixin):
    __tablename__ = "contests_participants"

    contest_id: Mapped[int] = mapped_column(
        ForeignKey("contests.contest_id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[BigInteger] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )


class UserModel(Base, TimestampMixin):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=False
    )
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str | None] = mapped_column(nullable=True)
    username: Mapped[str | None] = mapped_column(nullable=True)
    photo_id: Mapped[str | None] = mapped_column(nullable=True)

    contests: Mapped[list["ContestModel"]] = relationship(
        "ContestModel",
        secondary="contests_participants",
        back_populates="participants",
    )


class ChatModel(Base, TimestampMixin):
    __tablename__ = "chats"

    chat_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=False
    )
    title: Mapped[str | None] = mapped_column(nullable=True)
    username: Mapped[str | None] = mapped_column(nullable=True)

    contests: Mapped[list["ContestModel"]] = relationship(
        "ContestModel", back_populates="chat", cascade="all, delete"
    )


class ContestModel(Base, TimestampMixin):
    __tablename__ = "contests"

    contest_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )
    chat_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chats.chat_id", ondelete="CASCADE"),
        nullable=False,
    )
    current_round: Mapped[int] = mapped_column(default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    creator_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    chat: Mapped["ChatModel"] = relationship(
        "ChatModel", back_populates="contests"
    )
    participants: Mapped[list["UserModel"]] = relationship(
        "UserModel",
        secondary="contests_participants",
        back_populates="contests",
    )
    rounds: Mapped[list["RoundModel"]] = relationship(
        "RoundModel", back_populates="contest", cascade="all, delete"
    )


class RoundModel(Base, TimestampMixin):
    __tablename__ = "rounds"

    round_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
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

    match_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    round_id: Mapped[int] = mapped_column(
        ForeignKey("rounds.round_id", ondelete="CASCADE"), nullable=False
    )

    user1_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    user2_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
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
