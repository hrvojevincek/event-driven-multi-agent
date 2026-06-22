from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from eventforge.events.schemas.constants import (
    DETAIL_TYPE_KNOWLEDGE_MINED,
    KNOWLEDGE_MINED_SCHEMA_VERSION,
)
from eventforge.events.schemas.envelope import EventEnvelope


class KnowledgeMinedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_ids: list[UUID] = Field(min_length=1)
    entity_count: int = Field(ge=1)


class KnowledgeMinedEvent(EventEnvelope):
    detail_type: Literal["eventforge.knowledge.mined"] = DETAIL_TYPE_KNOWLEDGE_MINED
    schema_version: Literal["1.0"] = KNOWLEDGE_MINED_SCHEMA_VERSION
    payload: KnowledgeMinedPayload


def build_knowledge_mined_event(
    *,
    job_id: UUID,
    correlation_id: str,
    entity_ids: list[UUID],
    event_id: UUID | None = None,
    timestamp: datetime | None = None,
) -> KnowledgeMinedEvent:
    return KnowledgeMinedEvent(
        event_id=event_id or uuid4(),
        correlation_id=correlation_id,
        job_id=job_id,
        timestamp=timestamp or datetime.now(tz=UTC),
        payload=KnowledgeMinedPayload(
            entity_ids=entity_ids,
            entity_count=len(entity_ids),
        ),
    )
