import typing

from loguru import logger

from app.bot.router import Router
from app.poller.schemas import (
    Update,
    InlineKeyboard,
    InlineKeyboardButton,
    UserProfilePhotos,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application

router = Router()


@router.callback("apply")
async def apply(app: "Application", update: Update):
    photos: UserProfilePhotos = await app.store.bot.get_user_profile_photos(
        update.callback_query.from_user.id, limit=1
    )

    if photos.total_count == 0:
        await app.store.bot.answer_callback_query(
            update.callback_query.id,
            "⚠️ Для участия в игре необходимо установить автатарку.",
            show_alert=True,
        )
        return

    photo_sizes = photos.photos[0]
    largest_photo = photo_sizes[-1]
    file_id = largest_photo.file_id

    user = await app.store.db.get_or_create_user(
        user_id=update.callback_query.from_user.id,
        first_name=update.callback_query.from_user.first_name,
        last_name=update.callback_query.from_user.last_name,
        username=update.callback_query.from_user.username,
        photo_id=None,
    )
    user = await app.store.db.update_user_photo(
        user_id=user.user_id, photo_id=file_id
    )

    contest = await app.store.db.get_active_contest_by_chat_id(
        update.callback_query.message.chat.id
    )

    user_added = await app.store.db.add_user_to_contest(
        user.user_id, contest.contest_id
    )
    if not user_added:
        return

    participants = await app.store.db.get_contest_participants(
        contest.contest_id
    )

    participants_text = "".join(
        [
            f"{participant.last_name or ''} {participant.first_name}\n"
            for participant in participants
        ]
    )

    text = update.callback_query.message.text + (
        "\n\nУчастники:\n" f"{participants_text}"
    )

    await app.store.bot.edit_message_text(
        update.callback_query.message.chat.id,
        message_id=update.callback_query.message.message_id,
        text=text,
        reply_markup=update.callback_query.message.reply_markup,
    )


@router.callback("dismiss")
async def dismiss(app: "Application", update: Update):
    await app.store.bot.edit_message_text(
        update.callback_query.message.chat.id,
        message_id=update.callback_query.message.message_id,
        text="dissmis",
        reply_markup=update.callback_query.message.reply_markup,
    )


@router.callback("stop_game")
async def stop_game(app: "Application", update: Update):
    await app.store.bot.send_message(
        update.callback_query.message.chat.id,
        text="stop_game",
        reply_markup=update.callback_query.message.reply_markup,
    )
    active_contest = await app.store.db.get_active_contest_by_chat_id(
        update.callback_query.message.chat.id
    )
    await app.store.db.deactivate_contest(active_contest.contest_id)


@router.callback("cancel_game")
async def cancel_game(app: "Application", update: Update):
    await app.store.bot.send_message(
        update.callback_query.message.chat.id,
        text="cancel_game",
        reply_markup=update.callback_query.message.reply_markup,
    )
