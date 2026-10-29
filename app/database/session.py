"""Database session helpers."""

from app.database.base import session_factory


def get_session():
    """Return a new asynchronous database session context manager."""
    return session_factory()

