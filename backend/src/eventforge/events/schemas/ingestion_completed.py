from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from eventforge.events.schemas.constants import (
    DETAIL_TYPE_INGESTION_COMPLETED,
    INGESTION_COMPLETED_SCHEMA_VERSION,
)
from eventforge.events.schemas.envelope import EventEnvelope


class IngestionCompletedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_ids: list[UUID] = Field(min_length=1)
    source_count: int = Field(ge=1)


class IngestionCompletedEvent(EventEnvelope):
    detail_type: Literal["eventforge.ingestion.completed"] = DETAIL_TYPE_INGESTION_COMPLETED
    schema_version: Literal["1.0"] = INGESTION_COMPLETED_SCHEMA_VERSION
    payload: IngestionCompletedPayload


def build_ingestion_completed_event(
    *,
    job_id: UUID,
    correlation_id: str,
    source_ids: list[UUID],
    event_id: UUID | None = None,
    timestamp: datetime | None = None,
) -> IngestionCompletedEvent:
    return IngestionCompletedEvent(
        event_id=event_id or uuid4(),
        correlation_id=correlation_id,
        job_id=job_id,
        timestamp=timestamp or datetime.now(tz=UTC),
        payload=IngestionCompletedPayload(
            source_ids=source_ids,
            source_count=len(source_ids),
        ),
    )
