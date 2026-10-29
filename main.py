"""Application entry point for the Playlist Music Bot."""

import asyncio

from app.bot import create_bot, create_dispatcher
from app.database.base import init_db


async def main() -> None:
    """Start the bot and listen for Telegram updates."""
    await init_db()
    bot = create_bot()
    dispatcher = create_dispatcher()

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

