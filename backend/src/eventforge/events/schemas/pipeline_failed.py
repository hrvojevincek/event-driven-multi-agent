from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from eventforge.events.schemas.constants import (
    DETAIL_TYPE_PIPELINE_FAILED,
    PIPELINE_FAILED_SCHEMA_VERSION,
)
from eventforge.events.schemas.envelope import EventEnvelope


class PipelineFailedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: str = Field(min_length=1)
    failed_event_id: UUID
    failed_detail_type: str = Field(pattern=r"^eventforge\.")
    error_message: str = Field(min_length=1)
    source_queue: str | None = None
    receive_count: int | None = Field(default=None, ge=1)


class PipelineFailedEvent(EventEnvelope):
    detail_type: Literal["eventforge.pipeline.failed"] = DETAIL_TYPE_PIPELINE_FAILED
    schema_version: Literal["1.0"] = PIPELINE_FAILED_SCHEMA_VERSION
    payload: PipelineFailedPayload


def build_pipeline_failed_event(
    *,
    job_id: UUID,
    correlation_id: str,
    stage: str,
    failed_event_id: UUID,
    failed_detail_type: str,
    error_message: str,
    event_id: UUID,
    source_queue: str | None = None,
    receive_count: int | None = None,
    timestamp: datetime | None = None,
) -> PipelineFailedEvent:
    return PipelineFailedEvent(
        event_id=event_id,
        correlation_id=correlation_id,
        job_id=job_id,
        timestamp=timestamp or datetime.now(tz=UTC),
        payload=PipelineFailedPayload(
            stage=stage,
            failed_event_id=failed_event_id,
            failed_detail_type=failed_detail_type,
            error_message=error_message,
            source_queue=source_queue,
            receive_count=receive_count,
        ),
    )
