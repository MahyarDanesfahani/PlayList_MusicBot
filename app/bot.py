"""Telegram bot creation and update handlers."""

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from app.config import get_bot_token
from app.keyboards.language import language_keyboard


router = Router()
user_languages: dict[int, str] = {}


MESSAGES = {
    "fa": {
        "choose": "زبان خود را انتخاب کنید:",
        "welcome": (
            "سلام {name} 👋\n\n"
            "به بات پلی‌لیست موزیک خوش اومدی!\n"
            "به‌زودی می‌تونی پلی‌لیست‌های شخصی خودت رو بسازی و آهنگ‌هات رو مدیریت کنی."
        ),
    },
    "en": {
        "choose": "Please choose your language:",
        "welcome": (
            "Hello {name} 👋\n\n"
            "Welcome to the Music Playlist Bot!\n"
            "Soon you will be able to create personal playlists and manage your songs."
        ),
    },
}


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """Handle the /start command."""
    await message.answer(
        "زبان خود را انتخاب کنید / Please choose your language:",
        reply_markup=language_keyboard(),
    )


@router.callback_query(lambda callback: callback.data in {"language:fa", "language:en"})
async def language_handler(callback: CallbackQuery) -> None:
    """Save the selected language for the current process and show a welcome message."""
    if not callback.from_user or not callback.message or not callback.data:
        return

    language = callback.data.split(":", maxsplit=1)[1]
    user_languages[callback.from_user.id] = language
    first_name = callback.from_user.first_name or ("دوست" if language == "fa" else "friend")

    await callback.message.edit_text(MESSAGES[language]["welcome"].format(name=first_name))
    await callback.answer()


def create_dispatcher() -> Dispatcher:
    """Create and configure the update dispatcher."""
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    return dispatcher


def create_bot() -> Bot:
    """Create a Telegram bot using the configured token."""
    return Bot(token=get_bot_token())

