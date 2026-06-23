import uuid

from sqlalchemy import select

from eventforge.db.models import DocumentChunk
from eventforge.db.repositories.base import BaseRepository


class DocumentChunkRepository(BaseRepository):
    """Vector and relational access for document chunks."""

    async def search_similar(
        self,
        job_id: uuid.UUID,
        query_embedding: list[float],
        *,
        limit: int,
    ) -> list[DocumentChunk]:
        distance = DocumentChunk.embedding.cosine_distance(query_embedding)
        result = await self.session.execute(
            select(DocumentChunk)
            .where(DocumentChunk.job_id == job_id)
            .order_by(distance)
            .limit(limit)
        )
        return list(result.scalars().all())
