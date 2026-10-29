"""Keyboards related to language selection."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def language_keyboard() -> InlineKeyboardMarkup:
    """Return the language selection keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇮🇷 فارسی", callback_data="language:fa"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="language:en"),
            ]
        ]
    )

