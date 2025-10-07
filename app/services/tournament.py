import random
import typing
import pytz
from collections import deque
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.db.models import *

if typing.TYPE_CHECKING:
    from app.web.app import Application


class TournamentService:
    def __init__(self, app: "Application"):
        self.app = app

    def generate_bracket(
        self, participants: list
    ) -> list[tuple[UserModel, UserModel]]:
        random.shuffle(participants)
        bracket = []

        if len(participants) % 2 != 0:
            bye_participant = participants.pop()
            bracket.append((bye_participant, None))

        for i in range(0, len(participants), 2):
            if i + 1 < len(participants):
                bracket.append((participants[i], participants[i + 1]))

        return bracket

    async def start_contest(self, contest_id: int):
        contest = await self.app.store.db.get_contest_by_id(contest_id)

        moscow_tz = pytz.timezone("Europe/Moscow")
        now_moscow = datetime.now(moscow_tz)

        if now_moscow < contest.registration_deadline:
            raise ValueError("Не возможно начать игру, регистрация ещё идёт")

        participants = await self.app.store.db.get_contest_participants(
            contest_id
        )

        if len(participants) < 2:
            raise ValueError("Недостаточно участников для начала конкурса")

        # Создаем первый раунд
        round_model = await self.app.store.db.create_round(contest_id, 1)

        # Генерируем пары для первого раунда
        bracket = self.generate_bracket(participants)

        # Создаем матчи
        for user1, user2 in bracket:
            if user2:  # Обычный матч
                await self.app.store.db.create_match(
                    round_model.round_id, user1.user_id, user2.user_id
                )
            else:  # Автоматический проход
                # Создаем фиктивный матч где победитель известен сразу
                match = await self.app.store.db.create_match(
                    round_model.round_id, user1.user_id, user1.user_id
                )
                await self.app.store.db.finish_match(
                    match.match_id, user1.user_id
                )

    async def get_next_match(self, contest_id: int) -> tuple | None:
        current_match = await self.app.store.db.get_current_match(contest_id)

        if not current_match:
            # Проверяем, нужно ли создавать следующий раунд
            await self._create_next_round_if_needed(contest_id)
            current_match = await self.app.store.db.get_current_match(
                contest_id
            )

        return current_match

    async def _create_next_round_if_needed(self, contest_id: int):
        # Получаем текущий раунд
        async with self.app.store.db.app.database.sessionmaker() as session:
            contest = await self.app.store.db.get_contest_by_id(contest_id)

            current_round_number = contest.current_round
            current_round = next(
                (
                    r
                    for r in contest.rounds
                    if r.round_number == current_round_number
                ),
                None,
            )

            if current_round and self._is_round_finished(current_round):
                # Получаем победителей текущего раунда
                winners = []
                for match in current_round.matches:
                    if match.winner_id:
                        winners.append(match.winner_id)

                if len(winners) > 1:
                    # Создаем следующий раунд
                    new_round_number = current_round_number + 1
                    new_round = await self.app.store.db.create_round(
                        contest_id, new_round_number
                    )

                    # Создаем матчи для нового раунда
                    winners_objects = []
                    for winner_id in winners:
                        query_user = select(UserModel).where(
                            UserModel.user_id == winner_id
                        )
                        result_user = await session.execute(query_user)
                        winners_objects.append(result_user.scalar_one())

                    new_bracket = self.generate_bracket(winners_objects)
                    for user1, user2 in new_bracket:
                        if user2:
                            await self.app.store.db.create_match(
                                new_round.round_id, user1.user_id, user2.user_id
                            )

                    # Обновляем текущий раунд конкурса
                    contest.current_round = new_round_number

    def _is_round_finished(self, round_model: RoundModel) -> bool:
        return all(match.is_finished for match in round_model.matches)
