from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eventforge.db.models import DocumentChunk, Job, JobStageName, KnowledgeEntity
from eventforge.db.repositories import (
    JobRepository,
    JobStageRepository,
    KnowledgeEntityRepository,
    ProcessedEventRepository,
)
from eventforge.events.deterministic import deterministic_event_id
from eventforge.events.publisher import EVENT_SOURCE_KNOWLEDGE, EventPublisher, EventPublishError
from eventforge.events.schemas import (
    DETAIL_TYPE_KNOWLEDGE_MINED,
    WORKER_NAME_KNOWLEDGE,
    EmbeddingCompletedEvent,
    KnowledgeMinedEvent,
    build_knowledge_mined_event,
)
from eventforge.events.schemas.constants import DETAIL_TYPE_EMBEDDING_COMPLETED


def _entity_name_from_chunk(chunk: DocumentChunk) -> str:
    words = chunk.content.split()
    if not words:
        return f"concept-{chunk.chunk_index + 1}"
    return " ".join(words[:4]).rstrip(".,;:")


def _mock_entities_for_job(job: Job, chunks: list[DocumentChunk]) -> list[KnowledgeEntity]:
    entities: list[KnowledgeEntity] = [
        KnowledgeEntity(
            job_id=job.id,
            chunk_id=None,
            name=job.topic[:512],
            entity_type="topic",
        )
    ]
    for chunk in chunks:
        entities.append(
            KnowledgeEntity(
                job_id=job.id,
                chunk_id=chunk.id,
                name=_entity_name_from_chunk(chunk),
                entity_type="concept",
            )
        )
    return entities


async def _load_or_create_entities(
    session: AsyncSession, job: Job, chunks: list[DocumentChunk]
) -> list[KnowledgeEntity]:
    entity_repo = KnowledgeEntityRepository(session)
    existing = await entity_repo.list_by_job_id(job.id)
    if existing:
        return existing

    entities = _mock_entities_for_job(job, chunks)
    session.add_all(entities)
    await session.flush()
    return entities


async def process_embedding_completed(
    session: AsyncSession,
    publisher: EventPublisher,
    event: EmbeddingCompletedEvent,
) -> KnowledgeMinedEvent | None:
    """Run knowledge mining for one embedding.completed event. Returns None if already processed."""
    processed_repo = ProcessedEventRepository(session)
    event_id = str(event.event_id)

    if not await processed_repo.try_claim(event_id, WORKER_NAME_KNOWLEDGE):
        return None

    job_repo = JobRepository(session)
    stage_repo = JobStageRepository(session)

    job = await job_repo.get_by_id(event.job_id)
    if job is None:
        msg = f"Job not found for knowledge mining: {event.job_id}"
        raise ValueError(msg)

    knowledge_stage = await stage_repo.get_by_job_and_stage(
        job.id, JobStageName.KNOWLEDGE_MINING.value
    )
    if knowledge_stage is None:
        msg = f"Knowledge mining stage missing for job: {job.id}"
        raise ValueError(msg)

    result = await session.execute(
        select(DocumentChunk)
        .where(DocumentChunk.id.in_(event.payload.chunk_ids))
        .order_by(DocumentChunk.source_id, DocumentChunk.chunk_index)
    )
    chunks = list(result.scalars().all())
    if len(chunks) != len(event.payload.chunk_ids):
        msg = f"Document chunks missing for knowledge mining job: {event.job_id}"
        raise ValueError(msg)

    await stage_repo.mark_running(knowledge_stage)
    entities = await _load_or_create_entities(session, job, chunks)

    completed_event = build_knowledge_mined_event(
        job_id=job.id,
        correlation_id=event.correlation_id,
        entity_ids=[entity.id for entity in entities],
        event_id=deterministic_event_id(job.id, DETAIL_TYPE_KNOWLEDGE_MINED),
    )

    await stage_repo.mark_completed(knowledge_stage)
    await session.commit()

    try:
        await publisher.publish(completed_event, source=EVENT_SOURCE_KNOWLEDGE)
    except EventPublishError:
        await processed_repo.release_claim(event_id, WORKER_NAME_KNOWLEDGE)
        await session.commit()
        raise

    return completed_event


def parse_embedding_completed_event(detail: dict) -> EmbeddingCompletedEvent:
    if detail.get("detail_type") != DETAIL_TYPE_EMBEDDING_COMPLETED:
        msg = f"Unexpected detail_type: {detail.get('detail_type')}"
        raise ValueError(msg)
    return EmbeddingCompletedEvent.model_validate(detail)
