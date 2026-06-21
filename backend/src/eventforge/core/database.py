import asyncpg

from eventforge.core.config import Settings


async def check_postgres(settings: Settings) -> None:
    conn = await asyncpg.connect(settings.database_url, timeout=5.0)
    try:
        await conn.execute("SELECT 1")
    finally:
        await conn.close()
