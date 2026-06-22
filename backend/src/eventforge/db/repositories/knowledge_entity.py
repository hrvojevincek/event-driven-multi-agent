import uuid

from sqlalchemy import select

from eventforge.db.models import KnowledgeEntity
from eventforge.db.repositories.base import BaseRepository


class KnowledgeEntityRepository(BaseRepository):
    async def list_by_job_id(self, job_id: uuid.UUID) -> list[KnowledgeEntity]:
        result = await self.session.execute(
            select(KnowledgeEntity)
            .where(KnowledgeEntity.job_id == job_id)
            .order_by(KnowledgeEntity.created_at)
        )
        return list(result.scalars().all())

    async def list_by_ids(self, entity_ids: list[uuid.UUID]) -> list[KnowledgeEntity]:
        if not entity_ids:
            return []
        result = await self.session.execute(
            select(KnowledgeEntity).where(KnowledgeEntity.id.in_(entity_ids))
        )
        return list(result.scalars().all())
