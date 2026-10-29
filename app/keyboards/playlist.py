"""Keyboards for playlist management."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu(language: str) -> InlineKeyboardMarkup:
    """Return the localized main menu."""
    if language == "en":
        labels = ("➕ New playlist", "📚 My playlists")
    else:
        labels = ("➕ پلی‌لیست جدید", "📚 پلی‌لیست‌های من")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=labels[0], callback_data="playlist:create")],
            [InlineKeyboardButton(text=labels[1], callback_data="playlist:list")],
        ]
    )


def playlist_actions(playlist_id: int, language: str) -> InlineKeyboardMarkup:
    """Return actions for one playlist."""
    delete_text = "🗑 Delete" if language == "en" else "🗑 حذف"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=delete_text,
                    callback_data=f"playlist:delete:{playlist_id}",
                )
            ]
        ]
    )

