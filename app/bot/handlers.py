import typing

from app.bot.router import Router
from app.poller.schemas import Update, InlineKeyboard, InlineKeyboardButton

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
    await app.store.bot.send_message(
        update.message.chat.id,
        f"<b>Мы начинаем регистрацию участников на игру!</b>\n\nУчаствуешь?",
        reply_markup=InlineKeyboard(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Участвую 👍", callback_data="apply"),
                    InlineKeyboardButton(text="Без меня 👎", callback_data="dismiss"),
                ]
            ]
        )
    )
