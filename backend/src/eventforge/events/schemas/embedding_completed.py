from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from eventforge.events.schemas.constants import (
    DETAIL_TYPE_EMBEDDING_COMPLETED,
    EMBEDDING_COMPLETED_SCHEMA_VERSION,
)
from eventforge.events.schemas.envelope import EventEnvelope


class EmbeddingCompletedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_ids: list[UUID] = Field(min_length=1)
    chunk_count: int = Field(ge=1)


class EmbeddingCompletedEvent(EventEnvelope):
    detail_type: Literal["eventforge.embedding.completed"] = DETAIL_TYPE_EMBEDDING_COMPLETED
    schema_version: Literal["1.0"] = EMBEDDING_COMPLETED_SCHEMA_VERSION
    payload: EmbeddingCompletedPayload


def build_embedding_completed_event(
    *,
    job_id: UUID,
    correlation_id: str,
    chunk_ids: list[UUID],
    event_id: UUID | None = None,
    timestamp: datetime | None = None,
) -> EmbeddingCompletedEvent:
    return EmbeddingCompletedEvent(
        event_id=event_id or uuid4(),
        correlation_id=correlation_id,
        job_id=job_id,
        timestamp=timestamp or datetime.now(tz=UTC),
        payload=EmbeddingCompletedPayload(
            chunk_ids=chunk_ids,
            chunk_count=len(chunk_ids),
        ),
    )
