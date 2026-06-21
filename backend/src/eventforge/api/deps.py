from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from eventforge.core.config import Settings, get_settings
from eventforge.db.session import get_session

__all__ = ["Settings", "get_db", "get_settings"]


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session
