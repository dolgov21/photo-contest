import typing

from app.bot.router import Router
from app.poller.schemas import Update, InlineKeyboard, InlineKeyboardButton

if typing.TYPE_CHECKING:
    from app.web.app import Application


router = Router()


@router.callback("apply")
async def apply(app: "Application", update: Update):
    await app.store.bot.edit_message_text(
        update.callback_query.message.chat.id,
        message_id=update.callback_query.message.message_id,
        text="apply",
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
