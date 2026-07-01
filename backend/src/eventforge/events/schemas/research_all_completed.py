from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from eventforge.events.schemas.constants import (
    DETAIL_TYPE_RESEARCH_ALL_COMPLETED,
    RESEARCH_ALL_COMPLETED_SCHEMA_VERSION,
)
from eventforge.events.schemas.envelope import EventEnvelope


class ResearchAllCompletedPayload(BaseModel):
    """Summary emitted after Step Functions waits for all research sub-tasks."""

    model_config = ConfigDict(extra="forbid")

    task_count: int = Field(ge=1)


class ResearchAllCompletedEvent(EventEnvelope):
    """Emitted when all research sub-tasks finish (eventforge.research.all_completed)."""

    detail_type: Literal["eventforge.research.all_completed"] = DETAIL_TYPE_RESEARCH_ALL_COMPLETED
    schema_version: Literal["1.0"] = RESEARCH_ALL_COMPLETED_SCHEMA_VERSION
    payload: ResearchAllCompletedPayload


def build_research_all_completed_event(
    *,
    job_id: UUID,
    correlation_id: str,
    task_count: int,
    event_id: UUID | None = None,
    timestamp: datetime | None = None,
) -> ResearchAllCompletedEvent:
    return ResearchAllCompletedEvent(
        event_id=event_id or uuid4(),
        correlation_id=correlation_id,
        job_id=job_id,
        timestamp=timestamp or datetime.now(tz=UTC),
        payload=ResearchAllCompletedPayload(task_count=task_count),
    )
