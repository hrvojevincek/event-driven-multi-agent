from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from eventforge.events.schemas.constants import (
    DETAIL_TYPE_SYNTHESIS_COMPLETED,
    SYNTHESIS_COMPLETED_SCHEMA_VERSION,
)
from eventforge.events.schemas.envelope import EventEnvelope


class SynthesisCompletedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: UUID
    note_count: int = Field(ge=1)


class SynthesisCompletedEvent(EventEnvelope):
    detail_type: Literal["eventforge.synthesis.completed"] = DETAIL_TYPE_SYNTHESIS_COMPLETED
    schema_version: Literal["1.0"] = SYNTHESIS_COMPLETED_SCHEMA_VERSION
    payload: SynthesisCompletedPayload


def build_synthesis_completed_event(
    *,
    job_id: UUID,
    correlation_id: str,
    report_id: UUID,
    note_count: int,
    event_id: UUID | None = None,
    timestamp: datetime | None = None,
) -> SynthesisCompletedEvent:
    return SynthesisCompletedEvent(
        event_id=event_id or uuid4(),
        correlation_id=correlation_id,
        job_id=job_id,
        timestamp=timestamp or datetime.now(tz=UTC),
        payload=SynthesisCompletedPayload(
            report_id=report_id,
            note_count=note_count,
        ),
    )
