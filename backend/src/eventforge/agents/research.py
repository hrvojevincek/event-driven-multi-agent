from sqlalchemy.ext.asyncio import AsyncSession

from eventforge.db.models import Job, JobStageName, KnowledgeEntity, ResearchNote
from eventforge.db.repositories import (
    JobRepository,
    JobStageRepository,
    KnowledgeEntityRepository,
    ProcessedEventRepository,
    ResearchNoteRepository,
)
from eventforge.events.deterministic import (
    deterministic_event_id,
    deterministic_research_task_id,
)
from eventforge.events.publisher import EVENT_SOURCE_RESEARCH, EventPublisher, EventPublishError
from eventforge.events.schemas import (
    DETAIL_TYPE_RESEARCH_TASK_COMPLETED,
    DETAIL_TYPE_RESEARCH_TASK_DISPATCHED,
    WORKER_NAME_RESEARCH,
    WORKER_NAME_RESEARCH_ORCHESTRATOR,
    KnowledgeMinedEvent,
    ResearchTaskCompletedEvent,
    ResearchTaskDispatchedEvent,
    build_research_task_completed_event,
    build_research_task_dispatched_event,
)
from eventforge.events.schemas.constants import DETAIL_TYPE_KNOWLEDGE_MINED
from eventforge.services.knowledge import (
    expected_research_task_count,
    research_entities_for_fanout,
)


def _sub_query_for_entity(job: Job, entity: KnowledgeEntity) -> str:
    return f"How does {entity.name} relate to {job.topic[:120]}?"


def _mock_research_note(job: Job, sub_query: str) -> str:
    return (
        f"Mock research findings for '{job.topic[:80]}'.\n"
        f"Sub-query: {sub_query}\n"
        "Key insight: stub note for Phase 2 pipeline validation."
    )


def _build_dispatched_events(
    event: KnowledgeMinedEvent,
    job: Job,
    entities: list[KnowledgeEntity],
) -> list[ResearchTaskDispatchedEvent]:
    research_targets = research_entities_for_fanout(entities)
    all_entity_ids = [entity.id for entity in entities]
    dispatched: list[ResearchTaskDispatchedEvent] = []
    for task_index, entity in enumerate(research_targets):
        task_id = deterministic_research_task_id(job.id, task_index)
        dispatched.append(
            build_research_task_dispatched_event(
                job_id=job.id,
                correlation_id=event.correlation_id,
                task_id=task_id,
                task_index=task_index,
                sub_query=_sub_query_for_entity(job, entity),
                entity_ids=all_entity_ids,
                event_id=deterministic_event_id(
                    job.id, f"{DETAIL_TYPE_RESEARCH_TASK_DISPATCHED}:{task_index}"
                ),
            )
        )
    return dispatched


async def _load_or_create_note(
    session: AsyncSession,
    job: Job,
    task: ResearchTaskDispatchedEvent,
) -> ResearchNote:
    note_repo = ResearchNoteRepository(session)
    existing = await note_repo.get_by_task_id(task.payload.task_id)
    if existing is not None:
        return existing

    note = ResearchNote(
        job_id=job.id,
        task_id=task.payload.task_id,
        task_index=task.payload.task_index,
        sub_query=task.payload.sub_query,
        content=_mock_research_note(job, task.payload.sub_query),
    )
    session.add(note)
    await session.flush()
    return note


async def process_knowledge_mined(
    session: AsyncSession,
    publisher: EventPublisher,
    event: KnowledgeMinedEvent,
) -> list[ResearchTaskDispatchedEvent] | None:
    """Fan out research sub-tasks from knowledge.mined. Returns None if already processed."""
    processed_repo = ProcessedEventRepository(session)
    event_id = str(event.event_id)

    if not await processed_repo.try_claim(event_id, WORKER_NAME_RESEARCH_ORCHESTRATOR):
        return None

    job_repo = JobRepository(session)
    stage_repo = JobStageRepository(session)
    entity_repo = KnowledgeEntityRepository(session)

    job = await job_repo.get_by_id(event.job_id)
    if job is None:
        msg = f"Job not found for research fan-out: {event.job_id}"
        raise ValueError(msg)

    research_stage = await stage_repo.get_by_job_and_stage(job.id, JobStageName.RESEARCH.value)
    if research_stage is None:
        msg = f"Research stage missing for job: {job.id}"
        raise ValueError(msg)

    entities = await entity_repo.list_by_ids(event.payload.entity_ids)
    if len(entities) != len(event.payload.entity_ids):
        msg = f"Knowledge entities missing for research job: {event.job_id}"
        raise ValueError(msg)

    await stage_repo.mark_running(research_stage)
    dispatched_events = _build_dispatched_events(event, job, entities)

    await session.commit()

    try:
        for dispatched in dispatched_events:
            await publisher.publish(dispatched, source=EVENT_SOURCE_RESEARCH)
    except EventPublishError:
        await processed_repo.release_claim(event_id, WORKER_NAME_RESEARCH_ORCHESTRATOR)
        await session.commit()
        raise

    return dispatched_events


async def process_research_task_dispatched(
    session: AsyncSession,
    publisher: EventPublisher,
    event: ResearchTaskDispatchedEvent,
) -> ResearchTaskCompletedEvent | None:
    """Run one research sub-task. Returns None if already processed."""
    processed_repo = ProcessedEventRepository(session)
    event_id = str(event.event_id)

    if not await processed_repo.try_claim(event_id, WORKER_NAME_RESEARCH):
        return None

    job_repo = JobRepository(session)
    stage_repo = JobStageRepository(session)
    note_repo = ResearchNoteRepository(session)
    entity_repo = KnowledgeEntityRepository(session)

    job = await job_repo.get_by_id(event.job_id)
    if job is None:
        msg = f"Job not found for research task: {event.job_id}"
        raise ValueError(msg)

    research_stage = await stage_repo.get_by_job_and_stage(job.id, JobStageName.RESEARCH.value)
    if research_stage is None:
        msg = f"Research stage missing for job: {job.id}"
        raise ValueError(msg)

    note = await _load_or_create_note(session, job, event)

    completed_event = build_research_task_completed_event(
        job_id=job.id,
        correlation_id=event.correlation_id,
        task_id=event.payload.task_id,
        note_id=note.id,
        task_index=event.payload.task_index,
        event_id=deterministic_event_id(
            job.id, f"{DETAIL_TYPE_RESEARCH_TASK_COMPLETED}:{event.payload.task_index}"
        ),
    )

    entities = await entity_repo.list_by_ids(event.payload.entity_ids)
    expected_tasks = expected_research_task_count(entities)
    note_count = await note_repo.count_by_job_id(job.id)
    if note_count >= expected_tasks:
        await stage_repo.mark_completed(research_stage)

    await session.commit()

    try:
        await publisher.publish(completed_event, source=EVENT_SOURCE_RESEARCH)
    except EventPublishError:
        await processed_repo.release_claim(event_id, WORKER_NAME_RESEARCH)
        await session.commit()
        raise

    return completed_event


def parse_knowledge_mined_event(detail: dict) -> KnowledgeMinedEvent:
    if detail.get("detail_type") != DETAIL_TYPE_KNOWLEDGE_MINED:
        msg = f"Unexpected detail_type: {detail.get('detail_type')}"
        raise ValueError(msg)
    return KnowledgeMinedEvent.model_validate(detail)


def parse_research_task_dispatched_event(detail: dict) -> ResearchTaskDispatchedEvent:
    if detail.get("detail_type") != DETAIL_TYPE_RESEARCH_TASK_DISPATCHED:
        msg = f"Unexpected detail_type: {detail.get('detail_type')}"
        raise ValueError(msg)
    return ResearchTaskDispatchedEvent.model_validate(detail)
