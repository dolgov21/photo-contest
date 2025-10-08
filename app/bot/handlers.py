import asyncio
import typing
from datetime import datetime

import pytz

from app.bot.router import Router
from app.poller.schemas import (
    InlineKeyboard,
    InlineKeyboardButton,
    InputMediaPhoto,
    ReplyParameters,
    Update,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application

router = Router()


@router.command("start")
async def start(app: "Application", update: Update):
    await app.store.bot.send_message(
        update.message.chat.id,
        "👋 Привет! Добро пожаловать в <b>Фотоконкурс</b>! 📸\n\n"
        "Бот устроит турнир на выбывание среди участников чата — "
        "кто победит, решит голосование! 🏆\n\n"
        "Отправь <code>/start_game</code>, чтобы начать первый раунд.",
        parse_mode="HTML",
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

    moscow_tz = pytz.timezone("Europe/Moscow")
    now_moscow = datetime.now(moscow_tz)

    if active_contest:
        deadline_moscow = active_contest.registration_deadline.astimezone(
            moscow_tz
        )
        formatted_deadline = deadline_moscow.strftime("%H:%M:%S")

        if active_contest.registration_deadline > now_moscow:
            await app.store.bot.send_message(
                update.message.chat.id,
                f"⏳ Регистрация на текущий фотоконкурс ещё идёт!\n"
                f"Пожалуйста, дождитесь её завершения — "
                f"окончание регистрации: <b>{formatted_deadline}</b>.",
                parse_mode="HTML",
                reply_parameters=ReplyParameters(
                    message_id=update.message.message_id
                ),
            )
        else:
            await app.store.db.deactivate_contest(active_contest.contest_id)

    contest = await app.store.db.create_contest(
        chat_id=chat.chat_id,
        creator_id=user.user_id,
        registration_duration=app.config.game.registration_time,
    )

    await app.store.bot.send_message(
        update.message.chat.id,
        f"📸 Новый фотоконкурс создан!\n\n"
        f"Регистрация участников открыта на <b>"
        f"{app.config.game.registration_time} секунд!</b> 🚀",
        parse_mode="HTML",
        reply_parameters=ReplyParameters(message_id=update.message.message_id),
    )

    deadline_moscow = contest.registration_deadline.astimezone(moscow_tz)
    formatted_deadline = deadline_moscow.strftime("%H:%M:%S")

    await app.store.bot.send_message(
        update.message.chat.id,
        "<b>🧩 Начинаем регистрацию!</b>\n\n"
        "Хочешь участвовать в фототурнире? Нажми кнопку ниже 👇\n\n"
        f"🕒 Регистрация закрывается в <b>{formatted_deadline}</b>.",
        parse_mode="HTML",
        reply_markup=InlineKeyboard(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Участвую",
                        callback_data=f"apply_{contest.contest_id}",
                    ),
                    InlineKeyboardButton(
                        text="❌ Пропущу",
                        callback_data=f"dismiss_{contest.contest_id}",
                    ),
                ]
            ]
        ),
    )

    async def wait_and_start_game():
        moscow_tz = pytz.timezone("Europe/Moscow")
        now_moscow = datetime.now(moscow_tz)

        delay = (contest.registration_deadline - now_moscow).total_seconds()
        await asyncio.sleep(max(0, delay))

        try:
            await app.store.services.start_contest(contest.contest_id)

            await app.store.bot.send_message(
                chat.chat_id,
                "🎯 Регистрация завершена!\n\n"
                "Турнир начинается прямо сейчас — "
                "готовьтесь выбирать лучшие аватарки! 🔥",
            )

            next_match_id = await app.store.services.get_next_match(
                contest.contest_id
            )

            if next_match_id:
                await send_match_for_voting(app, chat.chat_id, next_match_id)
        except ValueError as e:
            await app.store.bot.send_message(chat.chat_id, f"⚠️ {e!s}")

    app.loop.create_task(wait_and_start_game())


@router.command("cancel_game")
async def cancel_game(app: "Application", update: Update):
    active_contest = await app.store.db.get_active_contest_by_chat_id(
        update.message.chat.id
    )
    if not active_contest:
        await app.store.bot.send_message(
            update.message.chat.id,
            "⚠️ В этом чате нет активного конкурса.",
            reply_markup=ReplyParameters(message_id=update.message.message_id),
        )
        return

    if update.message.from_user.id != active_contest.creator_id:
        await app.store.bot.send_message(
            update.message.chat.id,
            "🚫 Только создатель конкурса может отменить игру.",
            reply_markup=ReplyParameters(message_id=update.message.message_id),
        )
        return

    await app.store.bot.send_message(
        update.message.chat.id,
        "🛑<b>Вы действительно хотите приостановить фотоконкурс?</b>\n\n"
        "Если остановите игру, турнир будет завершён досрочно.",
        reply_markup=InlineKeyboard(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Да", callback_data="cancel_game"
                    ),
                    InlineKeyboardButton(
                        text="☑️ Нет", callback_data="continue_game"
                    ),
                ]
            ]
        ),
    )


async def send_match_for_voting(
    app: "Application", chat_id: int, match_id: int
):
    match = await app.store.db.get_match_by_id(match_id)

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
        reply_markup=keyboard,
    )
    voting_message_id = voting_message.message_id

    # время для голосования
    await asyncio.sleep(app.config.game.voting_time)

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
        text=f"🏁 Победил {winner.first_name}!\n\n"
        f"Голоса: \n• {user1.first_name} - {votes1} "
        f"❤️ \n• {user2.first_name} - {votes2} 💙",
    )

    next_match_id = await app.store.services.get_next_match(
        updated_match.round.contest_id
    )
    if next_match_id:
        await send_match_for_voting(app, chat_id, next_match_id)
    else:
        await app.store.bot.send_message(chat_id, "🎉 Турнир завершен!")
