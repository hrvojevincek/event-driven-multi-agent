from sqlalchemy.ext.asyncio import AsyncSession

from eventforge.db.models import Job, JobStageName, JobStatus, ResearchNote, SynthesisReport
from eventforge.db.repositories import (
    JobRepository,
    JobStageRepository,
    ProcessedEventRepository,
    ResearchNoteRepository,
    SynthesisReportRepository,
)
from eventforge.events.deterministic import deterministic_event_id
from eventforge.events.publisher import EVENT_SOURCE_SYNTHESIS, EventPublisher, EventPublishError
from eventforge.events.schemas import (
    DETAIL_TYPE_SYNTHESIS_COMPLETED,
    MOCK_RESEARCH_TASK_COUNT,
    WORKER_NAME_SYNTHESIS,
    ResearchTaskCompletedEvent,
    SynthesisCompletedEvent,
    build_synthesis_completed_event,
)
from eventforge.events.schemas.constants import DETAIL_TYPE_RESEARCH_TASK_COMPLETED


def _mock_report_content(job: Job, notes: list[ResearchNote]) -> str:
    sections = [f"# Research Synthesis: {job.topic}", ""]
    for note in notes:
        sections.extend(
            [
                f"## Sub-query {note.task_index + 1}",
                "",
                f"**Question:** {note.sub_query}",
                "",
                note.content,
                "",
            ]
        )
    sections.append("_Mock synthesis report for Phase 2 pipeline validation._")
    return "\n".join(sections)


async def _load_or_create_report(
    session: AsyncSession, job: Job, notes: list[ResearchNote]
) -> SynthesisReport:
    report_repo = SynthesisReportRepository(session)
    existing = await report_repo.get_by_job_id(job.id)
    if existing is not None:
        return existing

    report = SynthesisReport(
        job_id=job.id,
        content=_mock_report_content(job, notes),
    )
    session.add(report)
    await session.flush()
    return report


async def process_research_task_completed(
    session: AsyncSession,
    publisher: EventPublisher,
    event: ResearchTaskCompletedEvent,
) -> SynthesisCompletedEvent | None:
    """Synthesize when all research notes exist. Returns None if skipped or already processed."""
    processed_repo = ProcessedEventRepository(session)
    event_id = str(event.event_id)

    if not await processed_repo.try_claim(event_id, WORKER_NAME_SYNTHESIS):
        return None

    job_repo = JobRepository(session)
    stage_repo = JobStageRepository(session)
    note_repo = ResearchNoteRepository(session)

    job = await job_repo.get_by_id(event.job_id)
    if job is None:
        msg = f"Job not found for synthesis: {event.job_id}"
        raise ValueError(msg)

    note_count = await note_repo.count_by_job_id(job.id)
    if note_count < MOCK_RESEARCH_TASK_COUNT:
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
    report = await _load_or_create_report(session, job, notes)

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
