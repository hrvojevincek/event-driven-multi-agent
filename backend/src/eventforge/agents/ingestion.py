from sqlalchemy.ext.asyncio import AsyncSession

from eventforge.db.models import Job, JobStageName, JobStatus, Source
from eventforge.db.repositories import JobRepository, JobStageRepository, ProcessedEventRepository
from eventforge.events.publisher import EVENT_SOURCE_INGESTION, EventPublisher, EventPublishError
from eventforge.events.schemas import (
    WORKER_NAME_INGESTION,
    IngestionCompletedEvent,
    QuerySubmittedEvent,
    build_ingestion_completed_event,
)
from eventforge.events.schemas.constants import DETAIL_TYPE_QUERY_SUBMITTED

DEFAULT_MOCK_SOURCE_COUNT = 3


def _mock_sources(job: Job, count: int) -> list[Source]:
    sources: list[Source] = []
    for index in range(1, count + 1):
        sources.append(
            Source(
                job_id=job.id,
                url=f"https://example.com/source/{job.id}/{index}",
                title=f"Mock source {index} for {job.topic[:80]}",
                snippet=f"Stub content about {job.topic[:120]} (source {index}).",
            )
        )
    return sources


async def process_query_submitted(
    session: AsyncSession,
    publisher: EventPublisher,
    event: QuerySubmittedEvent,
) -> IngestionCompletedEvent | None:
    """Run ingestion for one query.submitted event. Returns None if already processed."""
    processed_repo = ProcessedEventRepository(session)
    event_id = str(event.event_id)

    if await processed_repo.exists(event_id):
        return None

    job_repo = JobRepository(session)
    stage_repo = JobStageRepository(session)

    job = await job_repo.get_by_id(event.job_id)
    if job is None:
        msg = f"Job not found for ingestion: {event.job_id}"
        raise ValueError(msg)

    ingestion_stage = await stage_repo.get_by_job_and_stage(job.id, JobStageName.INGESTION.value)
    if ingestion_stage is None:
        msg = f"Ingestion stage missing for job: {job.id}"
        raise ValueError(msg)

    job.status = JobStatus.RUNNING.value
    await stage_repo.mark_running(ingestion_stage)

    source_count = job.max_sources or DEFAULT_MOCK_SOURCE_COUNT
    sources = _mock_sources(job, source_count)
    session.add_all(sources)
    await session.flush()

    completed_event = build_ingestion_completed_event(
        job_id=job.id,
        correlation_id=event.correlation_id,
        source_ids=[source.id for source in sources],
    )

    try:
        await publisher.publish(completed_event, source=EVENT_SOURCE_INGESTION)
    except EventPublishError:
        await session.rollback()
        raise

    await stage_repo.mark_completed(ingestion_stage)
    await processed_repo.record(event_id, WORKER_NAME_INGESTION)
    await session.commit()

    return completed_event


def parse_query_submitted_event(detail: dict) -> QuerySubmittedEvent:
    if detail.get("detail_type") != DETAIL_TYPE_QUERY_SUBMITTED:
        msg = f"Unexpected detail_type: {detail.get('detail_type')}"
        raise ValueError(msg)
    return QuerySubmittedEvent.model_validate(detail)
