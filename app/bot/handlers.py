import pytz
import typing
import asyncio
from datetime import datetime

from loguru import logger

from app.bot.router import Router
from app.db.models import MatchModel
from app.poller.schemas import (
    InlineKeyboard,
    InlineKeyboardButton,
    Update,
    ReplyParameters,
    InputMediaPhoto,
    Message,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application

router = Router()


@router.command("start")
async def start(app: "Application", update: Update):
    await app.store.bot.send_message(
        update.message.chat.id,
        f"Привет! Отправь /start_game, чтобы начать конкурс.",
    )


@router.command("start_game")
async def start_game(app: "Application", update: Update):
    chat = await app.store.db.get_or_create_chat(
        chat_id=update.message.chat.id,
        title=update.message.chat.title,
        username=update.message.chat.username,
    )
    user = await app.store.db.get_or_create_user(
        user_id=update.message.from_user.id,
        first_name=update.message.from_user.first_name,
        last_name=update.message.from_user.last_name,
        username=update.message.from_user.username,
    )

    active_contest = await app.store.db.get_active_contest_by_chat_id(
        chat.chat_id
    )

    if active_contest:
        moscow_tz = pytz.timezone("Europe/Moscow")
        now_moscow = datetime.now(moscow_tz)

        if active_contest.registration_deadline > now_moscow:
            await app.store.bot.send_message(
                update.message.chat.id,
                f"⏳ Регистрация на текущую игру ещё не завершена."
                f"Дождитесь окончания регистрации. {active_contest.registration_deadline}",
                reply_parameters=ReplyParameters(
                    message_id=update.message.message_id
                ),
            )
            return
        else:
            await app.store.db.deactivate_contest(active_contest.contest_id)

    contest = await app.store.db.create_contest(
        chat_id=chat.chat_id,
        creator_id=user.user_id,
        registration_duration=15,
    )

    await app.store.bot.send_message(
        update.message.chat.id,
        f"Новый конкурс создан! Регистрация открыта на 30 секунд.",
        reply_parameters=ReplyParameters(message_id=update.message.message_id),
    )

    await app.store.bot.send_message(
        update.message.chat.id,
        f"<b>Мы начинаем регистрацию участников на игру!</b>\n\nУчаствуешь?"
        f"Пройти регистрацию необходимо до {contest.registration_deadline}",
        reply_markup=InlineKeyboard(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Участвую 👍", callback_data="apply"
                    ),
                    InlineKeyboardButton(
                        text="Без меня 👎", callback_data="dismiss"
                    ),
                ]
            ]
        ),
    )

    async def wait_and_start_game():
        moscow_tz = pytz.timezone("Europe/Moscow")
        now_moscow = datetime.now(moscow_tz)

        delay = (contest.registration_deadline - now_moscow).total_seconds() + 3
        await asyncio.sleep(max(0, delay))

        try:
            await app.store.services.start_contest(contest.contest_id)
            await app.store.bot.send_message(
                chat.chat_id, "Регистрация завершена! Турнир начинается."
            )

            next_match = await app.store.services.get_next_match(
                contest.contest_id
            )
            if next_match:
                await send_match_for_voting(app, chat.chat_id, next_match)
        except ValueError as e:
            await app.store.bot.send_message(chat.chat_id, f"⚠️ {str(e)}")

    app.loop.create_task(wait_and_start_game())


@router.command("stop_game")
async def stop_game(app: "Application", update: Update):
    await app.store.bot.send_message(
        update.message.chat.id,
        f"<b>Вы хотите приостановить игру?</b>",
        reply_markup=InlineKeyboard(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Да ❌", callback_data="stop_game"
                    ),
                    InlineKeyboardButton(
                        text="Нет ☑️", callback_data="continue_game"
                    ),
                ]
            ]
        ),
    )


async def send_match_for_voting(
    app: "Application", chat_id: int, match: MatchModel
):
    user1 = match.user1
    user2 = match.user2

    keyboard = InlineKeyboard(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"❤️ {user1.first_name}",
                    callback_data=f"vote_{match.match_id}_{user1.user_id}",
                ),
                InlineKeyboardButton(
                    text=f"💙 {user2.first_name}",
                    callback_data=f"vote_{match.match_id}_{user2.user_id}",
                ),
            ]
        ]
    )

    media_list = [
        InputMediaPhoto(
            media=user1.photo_id,
        ),
        InputMediaPhoto(
            media=user2.photo_id,
        ),
    ]
    voting_message = await app.store.bot.send_media_group_with_keyboard(
        chat_id=chat_id,
        media=media_list,
        question_text="Голосуем! Чья фотка лучше?",
        reply_markup=keyboard
    )
    voting_message_id = voting_message.message_id

    # время для голосования 
    await asyncio.sleep(10)

    # Подсчет голосов из БД
    updated_match = await app.store.db.get_match_by_id(match.match_id)
    votes1 = updated_match.votes_user1
    votes2 = updated_match.votes_user2

    if votes1 > votes2:
        winner = updated_match.user1
    elif votes2 > votes1:
        winner = updated_match.user2
    else:
        winner = updated_match.user1  # ничья

    # заносим победителя в бд
    await app.store.db.finish_match(match.match_id, winner.user_id)

    await app.store.bot.edit_message_text(
        chat_id=chat_id,
        message_id=voting_message_id,
        text=f"🏁 Победил {winner.first_name}!\n\nГолоса: {user1.first_name} - {votes1} ❤️ | {user2.first_name} - {votes2} 💙",
    )

    # создаём следующий матч
    next_match = await app.store.services.get_next_match(
        updated_match.round.contest_id
    )
    if next_match:
        await send_match_for_voting(app, chat_id, next_match)
    else:
        await app.store.bot.send_message(chat_id, "🎉 Турнир завершен!")