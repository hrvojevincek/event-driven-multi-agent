from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from eventforge.db.models import ProcessedEvent
from eventforge.db.repositories.base import BaseRepository


class ProcessedEventRepository(BaseRepository):
    async def try_claim(self, event_id: str, worker_name: str) -> bool:
        """Atomically claim an event for a worker.

        Uses INSERT ... ON CONFLICT DO NOTHING so concurrent processors (or SQS
        redelivery) cannot both win. Returns True if this caller claimed the
        event, False if it was already claimed by the same worker.
        """
        stmt = (
            pg_insert(ProcessedEvent)
            .values(event_id=event_id, worker_name=worker_name)
            .on_conflict_do_nothing(index_elements=["event_id", "worker_name"])
            .returning(ProcessedEvent.event_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def release_claim(self, event_id: str, worker_name: str) -> None:
        """Remove a claim so a failed post-commit publish can be retried."""
        await self.session.execute(
            delete(ProcessedEvent).where(
                ProcessedEvent.event_id == event_id,
                ProcessedEvent.worker_name == worker_name,
            )
        )
        await self.session.flush()

    async def exists(self, event_id: str) -> bool:
        result = await self.session.execute(
            select(ProcessedEvent.event_id).where(ProcessedEvent.event_id == event_id)
        )
        return result.scalars().first() is not None

    async def get_by_event_id(self, event_id: str) -> ProcessedEvent | None:
        result = await self.session.execute(
            select(ProcessedEvent).where(ProcessedEvent.event_id == event_id)
        )
        return result.scalars().first()

    async def record(self, event_id: str, worker_name: str) -> ProcessedEvent:
        event = ProcessedEvent(event_id=event_id, worker_name=worker_name)
        self.session.add(event)
        await self.session.flush()
        return event
