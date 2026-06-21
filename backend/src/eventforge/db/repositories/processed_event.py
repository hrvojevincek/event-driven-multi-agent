from sqlalchemy import select

from eventforge.db.models import ProcessedEvent
from eventforge.db.repositories.base import BaseRepository


class ProcessedEventRepository(BaseRepository):
    async def exists(self, event_id: str) -> bool:
        result = await self.session.execute(
            select(ProcessedEvent.event_id).where(ProcessedEvent.event_id == event_id)
        )
        return result.scalar_one_or_none() is not None

    async def get_by_event_id(self, event_id: str) -> ProcessedEvent | None:
        result = await self.session.execute(
            select(ProcessedEvent).where(ProcessedEvent.event_id == event_id)
        )
        return result.scalar_one_or_none()
