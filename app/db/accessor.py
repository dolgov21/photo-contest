import typing
import pytz
from datetime import datetime, timedelta

from sqlalchemy import select, update, desc
from sqlalchemy.orm import selectinload
from loguru import logger

from app.db.models import *

if typing.TYPE_CHECKING:
    from app.web.app import Application


class DatabaseAccessor:
    def __init__(self, app: "Application"):
        self.app = app

    async def get_or_create_chat(
        self, chat_id: int, title: str, username: str
    ) -> ChatModel:
        async with self.app.database.sessionmaker() as session:
            query = select(ChatModel).where(ChatModel.chat_id == chat_id)
            result = await session.execute(query)
            chat = result.scalar_one_or_none()

            if not chat:
                chat = ChatModel(
                    chat_id=chat_id,
                    title=title,
                    username=username,
                )
                session.add(chat)
                await session.commit()
                await session.refresh(chat)
        return chat

    async def create_contest(
        self, chat_id: int, creator_id: int, registration_duration: int = 60
    ) -> ContestModel:
        moscow_tz = pytz.timezone("Europe/Moscow")
        now_moscow = datetime.now(moscow_tz)
        deadline = now_moscow + timedelta(seconds=registration_duration)
        contest = ContestModel(
            chat_id=chat_id,
            creator_id=creator_id,
            is_active=True,
            registration_deadline=deadline,
        )
        async with self.app.database.sessionmaker() as session:
            session.add(contest)
            await session.commit()
            await session.refresh(contest)
        return contest

    async def add_user_to_contest(self, user_id: int, contest_id: int) -> bool:
        async with self.app.database.sessionmaker() as session:
            moscow_tz = pytz.timezone("Europe/Moscow")
            now_moscow = datetime.now(moscow_tz)

            contest = await session.get(ContestModel, contest_id)
            if (
                contest.registration_deadline
                and now_moscow > contest.registration_deadline
            ):
                return False

            query = select(ContestsParticipantsModel).where(
                (ContestsParticipantsModel.contest_id == contest_id)
                & (ContestsParticipantsModel.user_id == user_id)
            )
            result = await session.execute(query)
            if result.scalar_one_or_none():
                return False

            contests_participant = ContestsParticipantsModel(
                contest_id=contest_id, user_id=user_id
            )
            session.add(contests_participant)
            await session.commit()
            return True

    async def get_active_contest_by_chat_id(
        self, chat_id: int
    ) -> ContestModel | None:
        async with self.app.database.sessionmaker() as session:
            query = (
                select(ContestModel)
                .where(
                    (ContestModel.chat_id == chat_id)
                    & (ContestModel.is_active == True)
                )
                .order_by(desc(ContestModel.recorded_at))
                .options(selectinload(ContestModel.rounds))
            )
            result = await session.execute(query)
            active_contests = result.scalars().all()

            if not active_contests:
                return None

            latest_contest = active_contests[0]

            # деактивируем, если по какой то причине активных тестов > 1
            if len(active_contests) > 1:
                inactive_ids = [c.contest_id for c in active_contests[1:]]
                stmt = (
                    update(ContestModel)
                    .where(ContestModel.contest_id.in_(inactive_ids))
                    .values(is_active=False)
                )
                await session.execute(stmt)
                await session.commit()

            return latest_contest

    async def get_contest_by_id(self, contest_id: int) -> ContestModel:
        async with self.app.database.sessionmaker() as session:
            query = (
                select(ContestModel)
                .where((ContestModel.contest_id == contest_id))
                .options(selectinload(ContestModel.rounds))
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def deactivate_contest(self, contest_id: int):
        async with self.app.database.sessionmaker() as session:
            stmt = (
                update(ContestModel)
                .where(ContestModel.contest_id == contest_id)
                .values(is_active=False)
            )
            await session.execute(stmt)
            await session.commit()

    async def get_or_create_user(
        self,
        user_id: int,
        first_name: str,
        last_name: str = None,
        username: str = None,
        photo_id: str = None,
    ) -> UserModel:
        async with self.app.database.sessionmaker() as session:
            query = select(UserModel).where(UserModel.user_id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                user = UserModel(
                    user_id=user_id,
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    photo_id=photo_id,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
            return user

    async def update_user_photo(self, user_id: int, photo_id: str) -> UserModel:
        async with self.app.database.sessionmaker() as session:
            query = select(UserModel).where(UserModel.user_id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                raise ValueError(f"Пользователь с ID {user_id} не найден")

            user.photo_id = photo_id
            await session.commit()
            await session.refresh(user)
            return user

    async def get_contest_participants(
        self, contest_id: int
    ) -> list[UserModel]:
        async with self.app.database.sessionmaker() as session:
            query = (
                select(UserModel)
                .join(
                    ContestsParticipantsModel,
                    UserModel.user_id == ContestsParticipantsModel.user_id,
                )
                .where(ContestsParticipantsModel.contest_id == contest_id)
            )
            result = await session.execute(query)
            return list(result.scalars().all())

    async def create_round(
        self, contest_id: int, round_number: int
    ) -> RoundModel:
        async with self.app.database.sessionmaker() as session:
            round_model = RoundModel(
                contest_id=contest_id,
                round_number=round_number,
                is_finished=False,
            )
            session.add(round_model)

            stmt = (
                update(ContestModel)
                .where(ContestModel.contest_id == contest_id)
                .values(current_round=round_number)
            )
            await session.execute(stmt)

            await session.commit()
            await session.refresh(round_model)
            return round_model

    async def create_match(
        self, round_id: int, user1_id: int, user2_id: int
    ) -> MatchModel:
        async with self.app.database.sessionmaker() as session:
            match = MatchModel(
                round_id=round_id,
                user1_id=user1_id,
                user2_id=user2_id,
            )
            session.add(match)
            await session.commit()
            await session.refresh(match)
            return match

    async def get_match_by_id(self, match_id: int) -> MatchModel:
        async with self.app.database.sessionmaker() as session:
            query = select(MatchModel).where(MatchModel.match_id == match_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def update_votes(self, match_id: int, v1: int, v2: int):
        async with self.app.database.sessionmaker() as session:
            stmt = (
                update(MatchModel)
                .where(MatchModel.match_id == match_id)
                .values(votes_user1=v1, votes_user2=v2)
            )
            await session.execute(stmt)
            await session.commit()

    async def already_voted(self, match_id: int, voter_id: int) -> int | None:
        """
        Проверяет, голосовал ли пользователь в данном матче.
        Возвращает voted_for_id, если голос есть, иначе None.
        """
        async with self.app.database.sessionmaker() as session:
            query = select(VoteModel).where(
                (VoteModel.match_id == match_id) &
                (VoteModel.voter_id == voter_id)
            )
            result = await session.execute(query)
            vote = result.scalar_one_or_none()
            return vote.voted_for_id if vote else None

    async def add_vote(self, match_id: int, voter_id: int, voted_for_id: int):
        async with self.app.database.sessionmaker() as session:
            # Проверяем, существует ли матч
            query = select(MatchModel).where(MatchModel.match_id == match_id)
            result = await session.execute(query)
            match = result.scalar_one_or_none()

            if not match:
                raise ValueError(f"Match with id {match_id} not found")

            # Создаём запись о голосе
            vote = VoteModel(
                match_id=match_id,
                voter_id=voter_id,
                voted_for_id=voted_for_id,
            )
            session.add(vote)

            # Обновляем счёт
            if voted_for_id == match.user1_id:
                match.votes_user1 += 1
            elif voted_for_id == match.user2_id:
                match.votes_user2 += 1
            else:
                raise ValueError("Invalid voted_for_id")

            session.add(match)
            await session.commit()
            await session.refresh(match)

            return match

    async def finish_match(self, match_id: int, winner_id: int) -> None:
        async with self.app.database.sessionmaker() as session:
            stmt = (
                update(MatchModel)
                .where(MatchModel.match_id == match_id)
                .values(winner_id=winner_id, is_finished=True)
            )
            await session.execute(stmt)
            await session.commit()

    async def get_current_match(self, contest_id: int) -> MatchModel | None:
        async with self.app.database.sessionmaker() as session:
            query = (
                select(MatchModel)
                .join(MatchModel.round)
                .join(RoundModel.contest)
                .options(
                    selectinload(MatchModel.user1),
                    selectinload(MatchModel.user2),
                    selectinload(MatchModel.round).selectinload(RoundModel.contest),
                    # selectinload(MatchModel.votes)
                )
                .where(
                    ContestModel.contest_id == contest_id,
                    RoundModel.round_number == ContestModel.current_round,
                    MatchModel.winner_id.is_(None),
                    MatchModel.is_finished == False
                )
                .order_by(MatchModel.match_id)
            )
            
            result = await session.execute(query)
            return result.scalar_one_or_none()
