import random
import typing
from collections import deque
from datetime import datetime, timedelta

import pytz
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models.game import (
    ContestModel,
    MatchModel,
    RoundModel,
    UserModel,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


class TournamentService:
    def __init__(self, app: "Application"):
        self.app = app

    def generate_bracket(
        self, participants: list[UserModel]
    ) -> list[tuple[UserModel, UserModel]]:
        logger.debug(
            f"participants: {[participant.first_name for participant in participants]}"
        )
        random.shuffle(participants)
        bracket = []

        if len(participants) % 2 != 0:
            bye_participant = participants.pop()
            bracket.append(
                (bye_participant, bye_participant)
            )  # Автоматический проход

        for i in range(0, len(participants), 2):
            if i + 1 < len(participants):
                bracket.append((participants[i], participants[i + 1]))
        logger.debug(
            f"bracket: {[(b[0].first_name if b[0] else 'BYE', b[1].first_name if b[1] else 'BYE') for b in bracket]}"
        )
        return bracket

    async def start_contest(self, contest_id: int):
        contest = await self.app.store.db.get_contest_by_id(contest_id)

        moscow_tz = pytz.timezone("Europe/Moscow")
        now_moscow = datetime.now(moscow_tz)

        if now_moscow + timedelta(seconds=2) < contest.registration_deadline:
            raise ValueError("Не возможно начать игру, регистрация ещё идёт")

        participants = await self.app.store.db.get_contest_participants(
            contest_id
        )

        if len(participants) < 2:
            raise ValueError("Недостаточно участников для начала конкурса")

        round_model = await self.app.store.db.create_round(contest_id, 1)

        bracket = self.generate_bracket(participants)

        for user1, user2 in bracket:
            if user1 != user2:
                await self.app.store.db.create_match(
                    round_model.round_id, user1.user_id, user2.user_id
                )
            else:  # Автоматический проход (когда пользователей )
                match = await self.app.store.db.create_match(
                    round_model.round_id, user1.user_id, user1.user_id
                )
                await self.app.store.db.finish_match(
                    match.match_id, user1.user_id
                )

    async def get_next_match(self, contest_id: int) -> int | None:
        await self._create_next_round_if_needed(contest_id)

        current_match = await self.app.store.db.get_current_match(contest_id)

        if current_match:
            return current_match.match_id

        await self.app.store.db.get_contest_by_id(contest_id)
        current_round = await self.app.store.db.get_current_round(contest_id)

        if current_round and self._is_round_finished(current_round):
            winners = []
            for match in current_round.matches:
                if match.winner_id:
                    winners.append(match.winner_id)

            if len(winners) == 1:
                logger.info(
                    f"Tournament {contest_id} completed! Winner: {winners[0]}"
                )
                return None
            elif len(winners) == 0:
                logger.warning(f"Tournament {contest_id} has no winners!")
                return None

        return None

    async def _create_next_round_if_needed(self, contest_id: int) -> bool:
        """
        Создает следующий раунд если текущий завершен.
        Возвращает True если раунд был создан, False если нет.
        """
        try:
            async with self.app.store.db.app.database.sessionmaker() as session:
                # Явно загружаем конкурс с отношениями
                contest_query = (
                    select(ContestModel)
                    .options(
                        selectinload(ContestModel.rounds).selectinload(
                            RoundModel.matches
                        )
                    )
                    .where(ContestModel.contest_id == contest_id)
                )
                contest_result = await session.execute(contest_query)
                contest = contest_result.scalar_one_or_none()

                if not contest:
                    return False

                current_round_number = contest.current_round
                current_round = next(
                    (
                        r
                        for r in contest.rounds
                        if r.round_number == current_round_number
                    ),
                    None,
                )

                if not current_round:
                    return False

                if not self._is_round_finished(current_round):
                    return False

                winners = []
                for match in current_round.matches:
                    if match.winner_id and match.user1_id != match.user2_id:
                        winners.append(match.winner_id)

                # Если остался только один победитель - турнир завершен
                if len(winners) <= 1:
                    logger.info(
                        f"Tournament {contest_id} finished with {len(winners)} winner(s)"
                    )
                    return False

                # Создаем следующий раунд
                new_round_number = current_round_number + 1
                new_round = RoundModel(
                    contest_id=contest_id,
                    round_number=new_round_number,
                    is_finished=False,
                )
                session.add(new_round)
                await session.flush()  # Получаем round_id

                winners_query = select(UserModel).where(
                    UserModel.user_id.in_(winners)
                )
                winners_result = await session.execute(winners_query)
                winners_objects = winners_result.scalars().all()

                new_bracket = self.generate_bracket(winners_objects)
                logger.info(
                    f"Creating round {new_round_number} with {len(winners_objects)} winners: {[w.first_name for w in winners_objects]}"
                )

                for user1, user2 in new_bracket:
                    if user1 and user2:
                        if user1.user_id == user2.user_id:
                            # Автоматический проход
                            new_match = MatchModel(
                                round_id=new_round.round_id,
                                user1_id=user1.user_id,
                                user2_id=user1.user_id,
                                winner_id=user1.user_id,
                                is_finished=True,
                            )
                        else:
                            # Обычный матч
                            new_match = MatchModel(
                                round_id=new_round.round_id,
                                user1_id=user1.user_id,
                                user2_id=user2.user_id,
                                is_finished=False,
                            )
                        session.add(new_match)

                contest.current_round = new_round_number
                await session.commit()

                logger.info(
                    f"Created new round {new_round_number} for contest {contest_id}"
                )
                return True

        except Exception as e:
            logger.error(
                f"Error creating next round for contest {contest_id}: {e}"
            )
            await session.rollback()
            return False

    def _is_round_finished(self, round_model: RoundModel) -> bool:
        if not round_model.matches:
            return True
        return all(match.is_finished for match in round_model.matches)
