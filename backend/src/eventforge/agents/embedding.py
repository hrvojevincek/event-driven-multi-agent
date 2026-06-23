import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eventforge.core.config import get_settings
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
    WORKER_NAME_EMBEDDING,
    EmbeddingCompletedEvent,
    IngestionCompletedEvent,
    build_embedding_completed_event,
)
from eventforge.events.schemas.constants import DETAIL_TYPE_INGESTION_COMPLETED
from eventforge.services.embedding import (
    EmbeddingClient,
    build_source_text,
    chunk_text,
    get_embedding_client,
)


def _chunk_source_text(source: Source, *, chunk_size: int, overlap: int) -> list[str]:
    text = build_source_text(title=source.title, snippet=source.snippet)
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    if chunks:
        return chunks
    fallback = source.snippet.strip() or source.title.strip()
    return [fallback] if fallback else []


async def _build_chunks_for_sources(
    sources: list[Source],
    embed_client: EmbeddingClient,
    *,
    chunk_size: int,
    overlap: int,
) -> list[DocumentChunk]:
    pending: list[tuple[Source, int, str]] = []
    for source in sources:
        texts = _chunk_source_text(source, chunk_size=chunk_size, overlap=overlap)
        for chunk_index, content in enumerate(texts):
            pending.append((source, chunk_index, content))

    if not pending:
        msg = "No embeddable content found in sources"
        raise ValueError(msg)

    job_id = sources[0].job_id
    vectors = await embed_client.embed_texts(
        [content for _, _, content in pending],
        job_id=job_id,
        agent_name=WORKER_NAME_EMBEDDING,
    )

    return [
        DocumentChunk(
            job_id=source.job_id,
            source_id=source.id,
            chunk_index=chunk_index,
            content=content,
            embedding=vector,
        )
        for (source, chunk_index, content), vector in zip(pending, vectors, strict=True)
    ]


async def _load_or_create_chunks(
    session: AsyncSession,
    job_id: uuid.UUID,
    sources: list[Source],
    embed_client: EmbeddingClient | None = None,
    *,
    chunk_size: int,
    overlap: int,
) -> list[DocumentChunk]:
    result = await session.execute(
        select(DocumentChunk)
        .where(DocumentChunk.job_id == job_id)
        .order_by(DocumentChunk.source_id, DocumentChunk.chunk_index)
    )
    existing = list(result.scalars().all())
    if existing:
        return existing

    client = embed_client or get_embedding_client(session=session)
    chunks = await _build_chunks_for_sources(
        sources,
        client,
        chunk_size=chunk_size,
        overlap=overlap,
    )
    session.add_all(chunks)
    await session.flush()
    return chunks


async def process_ingestion_completed(
    session: AsyncSession,
    publisher: EventPublisher,
    event: IngestionCompletedEvent,
    *,
    embed_client: EmbeddingClient | None = None,
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

    settings = get_settings()
    await stage_repo.mark_running(embedding_stage)
    chunks = await _load_or_create_chunks(
        session,
        job.id,
        sources,
        embed_client,
        chunk_size=settings.embedding_chunk_size_tokens,
        overlap=settings.embedding_chunk_overlap_tokens,
    )

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
