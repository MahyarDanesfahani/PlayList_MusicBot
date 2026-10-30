"""Keyboards used by the mood-based song recommendation flow."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def recommendation_keyboard(options: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """Build a one-column keyboard for a recommendation question."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"recommend:answer:{value}")]
            for label, value in options
        ]
    )

