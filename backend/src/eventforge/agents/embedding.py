import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eventforge.db.models import DocumentChunk, JobStageName, Source
from eventforge.db.repositories import (
    JobRepository,
    JobStageRepository,
    ProcessedEventRepository,
    SourceRepository,
)
from eventforge.events.deterministic import deterministic_event_id
from eventforge.events.publisher import EVENT_SOURCE_EMBEDDING, EventPublisher, EventPublishError
from eventforge.events.schemas import (
    DETAIL_TYPE_EMBEDDING_COMPLETED,
    MOCK_CHUNKS_PER_SOURCE,
    MOCK_EMBEDDING_DIMENSION,
    WORKER_NAME_EMBEDDING,
    EmbeddingCompletedEvent,
    IngestionCompletedEvent,
    build_embedding_completed_event,
)
from eventforge.events.schemas.constants import DETAIL_TYPE_INGESTION_COMPLETED


def _mock_embedding(source_id: uuid.UUID, chunk_index: int) -> list[float]:
    digest = hashlib.sha256(f"{source_id}:{chunk_index}".encode()).digest()
    return [
        (digest[index % len(digest)] / 255.0) * 2 - 1 for index in range(MOCK_EMBEDDING_DIMENSION)
    ]


def _mock_chunks_for_source(source: Source) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for chunk_index in range(MOCK_CHUNKS_PER_SOURCE):
        chunks.append(
            DocumentChunk(
                job_id=source.job_id,
                source_id=source.id,
                chunk_index=chunk_index,
                content=f"{source.snippet} (chunk {chunk_index + 1})",
                embedding=_mock_embedding(source.id, chunk_index),
            )
        )
    return chunks


async def _load_or_create_chunks(
    session: AsyncSession, job_id: uuid.UUID, sources: list[Source]
) -> list[DocumentChunk]:
    result = await session.execute(
        select(DocumentChunk)
        .where(DocumentChunk.job_id == job_id)
        .order_by(DocumentChunk.source_id, DocumentChunk.chunk_index)
    )
    existing = list(result.scalars().all())
    if existing:
        return existing

    chunks: list[DocumentChunk] = []
    for source in sources:
        chunks.extend(_mock_chunks_for_source(source))
    session.add_all(chunks)
    await session.flush()
    return chunks


async def process_ingestion_completed(
    session: AsyncSession,
    publisher: EventPublisher,
    event: IngestionCompletedEvent,
) -> EmbeddingCompletedEvent | None:
    """Run embedding for one ingestion.completed event. Returns None if already processed."""
    processed_repo = ProcessedEventRepository(session)
    event_id = str(event.event_id)

    if not await processed_repo.try_claim(event_id, WORKER_NAME_EMBEDDING):
        return None

    job_repo = JobRepository(session)
    stage_repo = JobStageRepository(session)
    source_repo = SourceRepository(session)

    job = await job_repo.get_by_id(event.job_id)
    if job is None:
        msg = f"Job not found for embedding: {event.job_id}"
        raise ValueError(msg)

    embedding_stage = await stage_repo.get_by_job_and_stage(job.id, JobStageName.EMBEDDING.value)
    if embedding_stage is None:
        msg = f"Embedding stage missing for job: {job.id}"
        raise ValueError(msg)

    sources = await source_repo.list_by_ids(event.payload.source_ids)
    if len(sources) != len(event.payload.source_ids):
        msg = f"Sources missing for embedding job: {event.job_id}"
        raise ValueError(msg)

    await stage_repo.mark_running(embedding_stage)
    chunks = await _load_or_create_chunks(session, job.id, sources)

    completed_event = build_embedding_completed_event(
        job_id=job.id,
        correlation_id=event.correlation_id,
        chunk_ids=[chunk.id for chunk in chunks],
        event_id=deterministic_event_id(job.id, DETAIL_TYPE_EMBEDDING_COMPLETED),
    )

    await stage_repo.mark_completed(embedding_stage)
    await session.commit()

    try:
        await publisher.publish(completed_event, source=EVENT_SOURCE_EMBEDDING)
    except EventPublishError:
        await processed_repo.release_claim(event_id, WORKER_NAME_EMBEDDING)
        await session.commit()
        raise

    return completed_event


def parse_ingestion_completed_event(detail: dict) -> IngestionCompletedEvent:
    if detail.get("detail_type") != DETAIL_TYPE_INGESTION_COMPLETED:
        msg = f"Unexpected detail_type: {detail.get('detail_type')}"
        raise ValueError(msg)
    return IngestionCompletedEvent.model_validate(detail)
