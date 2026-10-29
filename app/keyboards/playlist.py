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
    add_text = "➕ Add song" if language == "en" else "➕ افزودن آهنگ"
    songs_text = "🎵 Songs" if language == "en" else "🎵 آهنگ‌ها"
    delete_text = "🗑 Delete" if language == "en" else "🗑 حذف"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=add_text, callback_data=f"playlist:addsong:{playlist_id}")],
            [InlineKeyboardButton(text=songs_text, callback_data=f"playlist:songs:{playlist_id}")],
            [
                InlineKeyboardButton(
                    text=delete_text,
                    callback_data=f"playlist:delete:{playlist_id}",
                )
            ]
        ]
    )


def song_actions(song_id: int, language: str) -> InlineKeyboardMarkup:
    """Return actions for one song."""
    text = "🗑 Delete" if language == "en" else "🗑 حذف"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=f"song:delete:{song_id}")]
        ]
    )

