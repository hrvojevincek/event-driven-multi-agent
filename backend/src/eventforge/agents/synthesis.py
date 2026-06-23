from sqlalchemy.ext.asyncio import AsyncSession

from eventforge.db.models import Job, JobStageName, JobStatus, ResearchNote, SynthesisReport
from eventforge.db.repositories import (
    JobRepository,
    JobStageRepository,
    KnowledgeEntityRepository,
    ProcessedEventRepository,
    ResearchNoteRepository,
    SourceRepository,
    SynthesisReportRepository,
)
from eventforge.events.deterministic import deterministic_event_id
from eventforge.events.publisher import EVENT_SOURCE_SYNTHESIS, EventPublisher, EventPublishError
from eventforge.events.schemas import (
    DETAIL_TYPE_SYNTHESIS_COMPLETED,
    WORKER_NAME_SYNTHESIS,
    ResearchTaskCompletedEvent,
    SynthesisCompletedEvent,
    build_synthesis_completed_event,
)
from eventforge.events.schemas.constants import DETAIL_TYPE_RESEARCH_TASK_COMPLETED
from eventforge.services.knowledge import expected_research_task_count
from eventforge.services.llm.client import LLMClient, get_llm_client
from eventforge.services.synthesis import generate_synthesis_report


async def _load_or_create_report(
    session: AsyncSession,
    job: Job,
    notes: list[ResearchNote],
    *,
    llm_client: LLMClient,
) -> SynthesisReport:
    report_repo = SynthesisReportRepository(session)
    existing = await report_repo.get_by_job_id(job.id)
    if existing is not None:
        return existing

    sources = await SourceRepository(session).list_by_job_id(job.id)
    content = await generate_synthesis_report(llm_client, job, notes, sources)

    report = SynthesisReport(
        job_id=job.id,
        content=content,
    )
    session.add(report)
    await session.flush()
    return report


async def process_research_task_completed(
    session: AsyncSession,
    publisher: EventPublisher,
    event: ResearchTaskCompletedEvent,
    *,
    llm_client: LLMClient | None = None,
) -> SynthesisCompletedEvent | None:
    """Synthesize when all research notes exist. Returns None if skipped or already processed."""
    processed_repo = ProcessedEventRepository(session)
    event_id = str(event.event_id)

    if not await processed_repo.try_claim(event_id, WORKER_NAME_SYNTHESIS):
        return None

    job_repo = JobRepository(session)
    stage_repo = JobStageRepository(session)
    note_repo = ResearchNoteRepository(session)
    entity_repo = KnowledgeEntityRepository(session)
    llm_client = llm_client or get_llm_client(session=session)

    job = await job_repo.get_by_id(event.job_id)
    if job is None:
        msg = f"Job not found for synthesis: {event.job_id}"
        raise ValueError(msg)

    entities = await entity_repo.list_by_job_id(job.id)
    expected_tasks = expected_research_task_count(entities)
    note_count = await note_repo.count_by_job_id(job.id)
    if expected_tasks == 0 or note_count < expected_tasks:
        await processed_repo.release_claim(event_id, WORKER_NAME_SYNTHESIS)
        await session.commit()
        return None

    synthesis_key = str(deterministic_event_id(job.id, DETAIL_TYPE_SYNTHESIS_COMPLETED))
    if not await processed_repo.try_claim(synthesis_key, WORKER_NAME_SYNTHESIS):
        await session.commit()
        return None

    synthesis_stage = await stage_repo.get_by_job_and_stage(job.id, JobStageName.SYNTHESIS.value)
    if synthesis_stage is None:
        msg = f"Synthesis stage missing for job: {job.id}"
        raise ValueError(msg)

    notes = await note_repo.list_by_job_id(job.id)
    await stage_repo.mark_running(synthesis_stage)
    report = await _load_or_create_report(session, job, notes, llm_client=llm_client)

    completed_event = build_synthesis_completed_event(
        job_id=job.id,
        correlation_id=event.correlation_id,
        report_id=report.id,
        note_count=len(notes),
        event_id=deterministic_event_id(job.id, DETAIL_TYPE_SYNTHESIS_COMPLETED),
    )

    job.status = JobStatus.COMPLETED.value
    await stage_repo.mark_completed(synthesis_stage)
    await session.commit()

    try:
        await publisher.publish(completed_event, source=EVENT_SOURCE_SYNTHESIS)
    except EventPublishError:
        await processed_repo.release_claim(synthesis_key, WORKER_NAME_SYNTHESIS)
        await processed_repo.release_claim(event_id, WORKER_NAME_SYNTHESIS)
        await session.commit()
        raise

    return completed_event


def parse_research_task_completed_event(detail: dict) -> ResearchTaskCompletedEvent:
    if detail.get("detail_type") != DETAIL_TYPE_RESEARCH_TASK_COMPLETED:
        msg = f"Unexpected detail_type: {detail.get('detail_type')}"
        raise ValueError(msg)
    return ResearchTaskCompletedEvent.model_validate(detail)
