"""SQLAlchemy base and database engine setup."""

from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_database_url


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""


engine = create_async_engine(get_database_url(), echo=False)
session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Create database tables if they do not exist yet."""
    from app.models.playlist import Playlist  # noqa: F401
    from app.models.song import Song  # noqa: F401
    from app.models.user import User  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

