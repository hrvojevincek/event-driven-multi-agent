import uuid

from sqlalchemy import select

from eventforge.db.models import Source
from eventforge.db.repositories.base import BaseRepository


class SourceRepository(BaseRepository):
    async def list_by_job_id(self, job_id: uuid.UUID) -> list[Source]:
        result = await self.session.execute(
            select(Source).where(Source.job_id == job_id).order_by(Source.created_at)
        )
        return list(result.scalars().all())

    async def list_by_ids(self, source_ids: list[uuid.UUID]) -> list[Source]:
        if not source_ids:
            return []
        result = await self.session.execute(select(Source).where(Source.id.in_(source_ids)))
        return list(result.scalars().all())
