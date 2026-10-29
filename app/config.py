"""Application configuration loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite+aiosqlite:///./playlist_bot.db"
)


def get_bot_token() -> str:
    """Return the Telegram bot token or raise a helpful configuration error."""
    if not BOT_TOKEN or BOT_TOKEN == "your_telegram_bot_token_here":
        raise RuntimeError(
            "BOT_TOKEN is not configured. Copy .env.example to .env "
            "and add your Telegram bot token."
        )
    return BOT_TOKEN


def get_database_url() -> str:
    """Return the configured database connection URL."""
    return DATABASE_URL

