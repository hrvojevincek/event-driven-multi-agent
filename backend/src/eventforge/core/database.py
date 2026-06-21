from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from eventforge.core.config import Settings
from eventforge.db.session import get_engine


async def check_postgres(settings: Settings) -> None:
    engine: AsyncEngine = get_engine(settings)
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
