"""Telegram bot creation and update handlers."""

from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy import delete, select

from app.config import get_bot_token
from app.database.session import get_session
from app.keyboards.language import language_keyboard
from app.keyboards.playlist import main_menu, playlist_actions
from app.models.playlist import Playlist
from app.models.user import User


router = Router()
user_languages: dict[int, str] = {}


class PlaylistCreation(StatesGroup):
    """States used while creating a playlist."""

    waiting_for_name = State()


MESSAGES = {
    "fa": {
        "choose": "زبان خود را انتخاب کنید:",
        "welcome": (
            "سلام {name} 👋\n\n"
            "به بات پلی‌لیست موزیک خوش اومدی!\n"
            "به‌زودی می‌تونی پلی‌لیست‌های شخصی خودت رو بسازی و آهنگ‌هات رو مدیریت کنی."
        ),
            "menu": "از منوی زیر یک گزینه را انتخاب کن:",
            "ask_name": "نام پلی‌لیست جدید را ارسال کن:",
            "empty": "هنوز پلی‌لیستی نساختی.",
            "list": "پلی‌لیست‌های تو:",
            "created": "پلی‌لیست «{name}» ساخته شد.",
            "deleted": "پلی‌لیست حذف شد.",
    },
    "en": {
        "choose": "Please choose your language:",
        "welcome": (
            "Hello {name} 👋\n\n"
            "Welcome to the Music Playlist Bot!\n"
            "Soon you will be able to create personal playlists and manage your songs."
        ),
            "menu": "Choose an option from the menu:",
            "ask_name": "Send the name of your new playlist:",
            "empty": "You have not created any playlists yet.",
            "list": "Your playlists:",
            "created": "Playlist “{name}” was created.",
            "deleted": "Playlist deleted.",
    },
}


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """Handle the /start command."""
    if message.from_user:
        async with get_session() as session:
            user = await session.scalar(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            if user is None:
                session.add(
                    User(
                        telegram_id=message.from_user.id,
                        username=message.from_user.username,
                        first_name=message.from_user.first_name,
                    )
                )
                await session.commit()

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

    async with get_session() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        if user is not None:
            user.language = language
            user.username = callback.from_user.username
            user.first_name = callback.from_user.first_name
            await session.commit()

    await callback.message.edit_text(
        MESSAGES[language]["welcome"].format(name=first_name)
    )
    await callback.message.answer(
        MESSAGES[language]["menu"], reply_markup=main_menu(language)
    )
    await callback.answer()


async def get_user_language(telegram_id: int) -> str:
    """Get a user's saved language, falling back to Persian."""
    async with get_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        return user.language if user and user.language in MESSAGES else "fa"


@router.callback_query(lambda callback: callback.data == "playlist:create")
async def create_playlist_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Ask the user for a new playlist name."""
    if not callback.from_user or not callback.message:
        return
    language = await get_user_language(callback.from_user.id)
    await state.set_state(PlaylistCreation.waiting_for_name)
    await callback.message.answer(MESSAGES[language]["ask_name"])
    await callback.answer()


@router.message(PlaylistCreation.waiting_for_name)
async def create_playlist(message: Message, state: FSMContext) -> None:
    """Create a playlist from the user's text message."""
    if not message.from_user or not message.text:
        return
    name = message.text.strip()
    language = await get_user_language(message.from_user.id)

    if not name or len(name) > 100:
        await message.answer(
            "نام باید بین ۱ تا ۱۰۰ کاراکتر باشد."
            if language == "fa"
            else "The name must be between 1 and 100 characters."
        )
        return

    async with get_session() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        if user is None:
            return
        session.add(Playlist(user_id=user.id, name=name))
        await session.commit()

    await state.clear()
    await message.answer(MESSAGES[language]["created"].format(name=name), reply_markup=main_menu(language))


@router.callback_query(lambda callback: callback.data == "playlist:list")
async def list_playlists(callback: CallbackQuery) -> None:
    """Show the current user's playlists."""
    if not callback.from_user or not callback.message:
        return
    language = await get_user_language(callback.from_user.id)
    async with get_session() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        playlists = []
        if user:
            result = await session.scalars(
                select(Playlist).where(Playlist.user_id == user.id).order_by(Playlist.id)
            )
            playlists = list(result)

    if not playlists:
        await callback.message.answer(MESSAGES[language]["empty"], reply_markup=main_menu(language))
    else:
        await callback.message.answer(MESSAGES[language]["list"])
        for playlist in playlists:
            await callback.message.answer(
                f"🎵 {playlist.name}",
                reply_markup=playlist_actions(playlist.id, language),
            )
    await callback.answer()


@router.callback_query(lambda callback: callback.data and callback.data.startswith("playlist:delete:"))
async def delete_playlist(callback: CallbackQuery) -> None:
    """Delete a playlist only if it belongs to the current user."""
    if not callback.from_user or not callback.message or not callback.data:
        return
    playlist_id = int(callback.data.rsplit(":", maxsplit=1)[1])
    language = await get_user_language(callback.from_user.id)
    async with get_session() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        if user:
            await session.execute(
                delete(Playlist).where(
                    Playlist.id == playlist_id, Playlist.user_id == user.id
                )
            )
            await session.commit()
    await callback.message.edit_text(MESSAGES[language]["deleted"])
    await callback.answer()


def create_dispatcher() -> Dispatcher:
    """Create and configure the update dispatcher."""
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    return dispatcher


def create_bot() -> Bot:
    """Create a Telegram bot using the configured token."""
    return Bot(token=get_bot_token())

