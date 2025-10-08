import re
import typing
from datetime import datetime

import pytz

from app.bot.router import Router
from app.poller.schemes import Update, UserProfilePhotos

if typing.TYPE_CHECKING:
    from app.web.app import Application

router = Router()


@router.callback_startswith("apply")
async def apply(app: "Application", update: Update):
    contest_id = int(update.callback_query.data.split("_")[1])
    contest = await app.store.db.get_contest_by_id(contest_id)

    if not contest or not getattr(contest, "is_active", False):
        await app.store.bot.answer_callback_query(
            update.callback_query.id,
            "⚠️ Этот конкурс уже завершён или недоступен.",
            show_alert=False,
        )
        return

    moscow_tz = pytz.timezone("Europe/Moscow")
    now_moscow = datetime.now(moscow_tz)

    if contest.registration_deadline < now_moscow:
        await app.store.bot.answer_callback_query(
            update.callback_query.id,
            "🚫 Регистрация уже завершена.",
            show_alert=False,
        )
        return

    photos: UserProfilePhotos = await app.store.bot.get_user_profile_photos(
        update.callback_query.from_user.id, limit=1
    )

    if photos.total_count == 0:
        await app.store.bot.answer_callback_query(
            update.callback_query.id,
            "⚠️ Для участия в игре необходимо установить аватарку.",
            show_alert=True,
        )
        return

    largest_photo = photos.photos[0][-1]
    file_id = largest_photo.file_id

    user = await app.store.db.get_or_create_user(
        user_id=update.callback_query.from_user.id,
        first_name=update.callback_query.from_user.first_name,
        last_name=update.callback_query.from_user.last_name,
        username=update.callback_query.from_user.username,
    )
    await app.store.db.update_user_photo(user_id=user.user_id, photo_id=file_id)

    user_added = await app.store.db.add_user_to_contest(
        user.user_id, contest.contest_id
    )
    if not user_added:
        await app.store.bot.answer_callback_query(
            update.callback_query.id,
            "ℹ️ Ты уже участвуешь в этом конкурсе!",
            show_alert=False,
        )
        return

    participants = await app.store.db.get_contest_participants(
        contest.contest_id
    )
    participants_text = "\n".join(
        [f"• {p.first_name} {p.last_name or ''}".strip() for p in participants]
    )

    original_text = update.callback_query.message.text
    clean_text = re.split(r"\n+Участники:", original_text, maxsplit=1)[0]

    text = (
        f"{clean_text}\n\n<b>Участники:</b>\n"
        f"{participants_text or '— пока никто не зарегистрировался —'}"
    )

    try:
        await app.store.bot.edit_message_text(
            chat_id=update.callback_query.message.chat.id,
            message_id=update.callback_query.message.message_id,
            text=text,
            parse_mode="HTML",
            reply_markup=update.callback_query.message.reply_markup,
        )
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            raise

    await app.store.bot.answer_callback_query(
        update.callback_query.id,
        "✅ Ты успешно зарегистрировался в фотоконкурсе!",
        show_alert=False,
    )


@router.callback_startswith("dismiss")
async def dismiss(app: "Application", update: Update):
    chat_id = update.callback_query.message.chat.id

    # Получаем активный конкурс
    contest = await app.store.db.get_active_contest_by_chat_id(chat_id)
    if not contest or not getattr(contest, "is_active", False):
        await app.store.bot.answer_callback_query(
            update.callback_query.id,
            "⚠️ Конкурс уже завершён или недоступен.",
            show_alert=False,
        )
        return

    user_id = update.callback_query.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    is_participant = await app.store.db.is_user_in_contest(
        user_id, contest.contest_id
    )

    if is_participant:
        await app.store.db.remove_user_from_contest(user_id, contest.contest_id)
        msg = "❌ Ты отказался от участия в фотоконкурсе."
    else:
        msg = "ℹ️ Ты и так не участвуешь в этом конкурсе."

    await app.store.bot.answer_callback_query(
        update.callback_query.id,
        msg,
        show_alert=False,
    )

    # Обновляем список участников
    participants = await app.store.db.get_contest_participants(
        contest.contest_id
    )
    participants_text = "\n".join(
        [f"• {p.first_name} {p.last_name or ''}".strip() for p in participants]
    )

    original_text = update.callback_query.message.text
    clean_text = re.split(r"\n+Участники:", original_text, maxsplit=1)[0]

    text = (
        f"{clean_text}\n\n<b>Участники:</b>\n"
        f"{participants_text or '— пока никто не зарегистрировался —'}"
    )

    try:
        await app.store.bot.edit_message_text(
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            text=text,
            parse_mode="HTML",
            reply_markup=update.callback_query.message.reply_markup,
        )
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            raise


@router.callback("cancel_game")
async def cancel_game(app: "Application", update: Update):
    chat_id = update.callback_query.message.chat.id

    active_contest = await app.store.db.get_active_contest_by_chat_id(chat_id)
    if not active_contest:
        await app.store.bot.answer_callback_query(
            update.callback_query.id,
            "⚠️ В этом чате нет активного конкурса.",
            show_alert=True,
        )
        return

    if update.callback_query.from_user.id != active_contest.creator_id:
        await app.store.bot.answer_callback_query(
            update.callback_query.id,
            "🚫 Только создатель конкурса может отменить игру.",
            show_alert=True,
        )
        return

    await app.store.db.deactivate_contest(active_contest.contest_id)

    await app.store.bot.edit_message_text(
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id,
        text=(
            "❌ <b>Конкурс был отменён.</b>\n\n"
            "Все текущие матчи и регистрация участников прекращены."
        ),
    )

    await app.store.bot.answer_callback_query(
        update.callback_query.id,
        "Конкурс успешно отменён.",
        show_alert=False,
    )


@router.callback("continue_game")
async def continue_game(app: "Application", update: Update):
    chat_id = update.callback_query.message.chat.id

    # Проверяем активный конкурс
    active_contest = await app.store.db.get_active_contest_by_chat_id(chat_id)
    if not active_contest:
        await app.store.bot.answer_callback_query(
            update.callback_query.id,
            "⚠️ В этом чате нет активного конкурса.",
            show_alert=True,
        )
        return

    if update.callback_query.from_user.id != active_contest.creator_id:
        await app.store.bot.answer_callback_query(
            update.callback_query.id,
            "🚫 Только создатель конкурса может отменить игру.",
            show_alert=True,
        )
        return

    await app.store.db.deactivate_contest(active_contest.contest_id)

    await app.store.bot.edit_message_text(
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id,
        text=(
            "❌ <b>Конкурс был отменён.</b>\n\n"
            "Все текущие матчи и регистрация участников прекращены."
        ),
    )

    await app.store.bot.answer_callback_query(
        update.callback_query.id,
        "Конкурс успешно отменён.",
        show_alert=False,
    )


@router.callback_startswith("vote")
async def vote(app: "Application", update: Update):
    match_id, voter_for_id = map(int, update.callback_query.data.split("_")[1:])

    # Проверяем, голосовал ли уже
    existing_vote = await app.store.db.already_voted(
        match_id, update.callback_query.from_user.id
    )
    if existing_vote is not None:
        voted_for_user = await app.store.db.get_user_by_id(existing_vote)
        await app.store.bot.answer_callback_query(
            update.callback_query.id,
            f"⚠️ Вы уже проголосовали за {voted_for_user.first_name}.",
            show_alert=False,
        )
        return

    await app.store.db.add_vote(
        match_id=match_id,
        voter_id=update.callback_query.from_user.id,
        voted_for_id=voter_for_id,
    )

    voted_for_user = await app.store.db.get_user_by_id(voter_for_id)
    await app.store.bot.answer_callback_query(
        update.callback_query.id,
        f"✅ Вы проголосовали за {voted_for_user.first_name}.",
        show_alert=False,
    )
