import typing

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.db.models import *

if typing.TYPE_CHECKING:
    from app.web.app import Application


class DatabaseAccessor:
    def __init__(self, app: "Application"):
        self.app = app

    async def create_contest(self, chat_id: int) -> ContestModel:
        contest = ContestModel(chat_id=chat_id, is_active=True)
        async with self.app.database.sessionmaker() as session:
            session.add(contest)
            await session.commit()
            await session.refresh(contest)
        return contest

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

    async def create_round(
        self, contest_id: int, round_number: int
    ) -> RoundModel:
        round = RoundModel(contest_id=contest_id, round_number=round_number)
        async with self.app.database.sessionmaker() as session:
            session.add(round)
            await session.commit()
            await session.refresh(round)
        return round

    async def get_rounds_by_contest(self, contest_id: int) -> list[RoundModel]:
        async with self.app.database.sessionmaker() as session:
            query = (
                select(RoundModel)
                .where(RoundModel.contest_id == contest_id)
                .options(selectinload(RoundModel.matches))
            )
            result = await session.execute(query)
            return result.scalars().all()

    async def create_match(
        self, round_id: int, user1_id: int, user2_id: int
    ) -> MatchModel:
        match = MatchModel(
            round_id=round_id,
            user1_id=user1_id,
            user2_id=user2_id,
            votes_user1=0,
            votes_user2=0,
        )
        async with self.app.database.sessionmaker() as session:
            session.add(match)
            await session.commit()
            await session.refresh(match)
        return match

    async def add_vote(self, match_id: int, user_id: int) -> MatchModel | None:
        async with self.app.database.sessionmaker() as session:
            match = await session.get(MatchModel, match_id)
            if not match:
                return None

            if user_id == match.user1_id:
                stmt = (
                    update(MatchModel)
                    .where(MatchModel.match_id == match_id)
                    .values(votes_user1=MatchModel.votes_user1 + 1)
                )
            elif user_id == match.user2_id:
                stmt = (
                    update(MatchModel)
                    .where(MatchModel.match_id == match_id)
                    .values(votes_user2=MatchModel.votes_user2 + 1)
                )
            else:
                return None

            await session.execute(stmt)
            await session.commit()

            return await session.get(MatchModel, match_id)

    async def set_match_winner(self, match_id: int, winner_id: int):
        async with self.app.database.sessionmaker() as session:
            stmt = (
                update(MatchModel)
                .where(MatchModel.match_id == match_id)
                .values(winner_id=winner_id)
            )
            await session.execute(stmt)
            await session.commit()
