import logging
import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from eventforge.api.schemas.queries import JobStageResponse, QueryDetailResponse
from eventforge.db.models import Job, JobStage, JobStageName, JobStatus, StageStatus
from eventforge.db.repositories import JobRepository, ProcessedEventRepository, UserRepository
from eventforge.events.publisher import PUBLISHER_WORKER_NAME, EventPublisher
from eventforge.events.schemas import QueryDepth, build_query_submitted_event

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SubmitQueryResult:
    job_id: uuid.UUID
    correlation_id: str


async def submit_query(
    session: AsyncSession,
    publisher: EventPublisher,
    *,
    topic: str,
    depth: QueryDepth = QueryDepth.STANDARD,
    max_sources: int | None = None,
) -> SubmitQueryResult:
    user = await UserRepository(session).get_or_create_mock_user()

    job_id = uuid.uuid4()
    correlation_id = uuid.uuid4().hex

    job = Job(
        id=job_id,
        user_id=user.id,
        correlation_id=correlation_id,
        topic=topic,
        depth=depth.value,
        status=JobStatus.PENDING.value,
        max_sources=max_sources,
    )
    session.add(job)

    for stage_name in JobStageName:
        session.add(
            JobStage(
                job_id=job_id,
                stage=stage_name.value,
                status=StageStatus.PENDING.value,
            )
        )

    await session.flush()

    event = build_query_submitted_event(
        job_id=job_id,
        correlation_id=correlation_id,
        topic=topic,
        depth=depth,
        max_sources=max_sources,
    )

    processed_repo = ProcessedEventRepository(session)
    event_id = str(event.event_id)

    if await processed_repo.try_claim(event_id, PUBLISHER_WORKER_NAME):
        await publisher.publish_query_submitted(event)
    else:
        logger.info(
            "Skipped publish; query.submitted already claimed",
            extra={"event_id": event_id, "job_id": str(job_id), "correlation_id": correlation_id},
        )

    await session.commit()

    return SubmitQueryResult(job_id=job_id, correlation_id=correlation_id)


_STAGE_ORDER = {stage.value: index for index, stage in enumerate(JobStageName)}


def _job_to_detail_response(job: Job) -> QueryDetailResponse:
    stages = sorted(job.stages, key=lambda stage: _STAGE_ORDER.get(stage.stage, len(_STAGE_ORDER)))
    return QueryDetailResponse(
        job_id=job.id,
        correlation_id=job.correlation_id,
        topic=job.topic,
        depth=job.depth,
        status=job.status,
        max_sources=job.max_sources,
        created_at=job.created_at,
        updated_at=job.updated_at,
        stages=[
            JobStageResponse(
                stage=stage.stage,
                status=stage.status,
                started_at=stage.started_at,
                completed_at=stage.completed_at,
                duration_ms=stage.duration_ms,
                error_detail=stage.error_detail,
            )
            for stage in stages
        ],
    )


async def get_query_detail(session: AsyncSession, job_id: uuid.UUID) -> QueryDetailResponse | None:
    job = await JobRepository(session).get_by_id(job_id)
    if job is None:
        return None
    return _job_to_detail_response(job)
