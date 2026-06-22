import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from eventforge.agents.embedding import (
    parse_ingestion_completed_event,
    process_ingestion_completed,
)
from eventforge.core.config import get_settings
from eventforge.db.models import (
    DocumentChunk,
    Job,
    JobStage,
    JobStageName,
    JobStatus,
    Source,
    StageStatus,
    User,
)
from eventforge.db.repositories import ProcessedEventRepository
from eventforge.db.session import reset_engine
from eventforge.events.parser import parse_eventbridge_sqs_body
from eventforge.events.publisher import EventPublisher
from eventforge.events.schemas import (
    MOCK_CHUNKS_PER_SOURCE,
    WORKER_NAME_EMBEDDING,
    build_embedding_completed_event,
    build_ingestion_completed_event,
)
from eventforge.workers.embedding import EmbeddingWorker

settings = get_settings()


@pytest.fixture
async def db_session() -> AsyncSession:
    reset_engine()
    engine = create_async_engine(settings.async_database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()
    reset_engine()


async def _seed_job_with_sources(db_session: AsyncSession) -> tuple[Job, JobStage, list[Source]]:
    suffix = uuid.uuid4().hex[:8]
    user = User(email=f"embed-{suffix}@example.com", clerk_id=f"embed-user-{suffix}")
    db_session.add(user)
    await db_session.flush()

    job = Job(
        user_id=user.id,
        correlation_id=f"corr-embed-{suffix}",
        topic="Vector search patterns",
        depth="standard",
        status=JobStatus.RUNNING.value,
        max_sources=2,
    )
    db_session.add(job)
    await db_session.flush()

    embedding_stage = JobStage(
        job_id=job.id,
        stage=JobStageName.EMBEDDING.value,
        status=StageStatus.PENDING.value,
    )
    db_session.add(embedding_stage)

    sources = [
        Source(
            job_id=job.id,
            url=f"https://example.com/{job.id}/1",
            title="Source 1",
            snippet="First snippet about vectors.",
        ),
        Source(
            job_id=job.id,
            url=f"https://example.com/{job.id}/2",
            title="Source 2",
            snippet="Second snippet about embeddings.",
        ),
    ]
    db_session.add_all(sources)
    await db_session.flush()
    return job, embedding_stage, sources


def test_parse_ingestion_completed_event_rejects_wrong_type() -> None:
    with pytest.raises(ValueError, match="Unexpected detail_type"):
        parse_ingestion_completed_event({"detail_type": "eventforge.query.submitted"})


async def test_process_ingestion_completed_writes_chunks_and_updates_stage(
    db_session: AsyncSession,
) -> None:
    job, stage, sources = await _seed_job_with_sources(db_session)
    mock_publisher = AsyncMock(spec=EventPublisher)

    inbound = build_ingestion_completed_event(
        job_id=job.id,
        correlation_id=job.correlation_id,
        source_ids=[source.id for source in sources],
    )

    result = await process_ingestion_completed(db_session, mock_publisher, inbound)

    assert result is not None
    assert result.payload.chunk_count == len(sources) * MOCK_CHUNKS_PER_SOURCE
    mock_publisher.publish.assert_awaited_once()

    await db_session.refresh(stage)
    assert stage.status == StageStatus.COMPLETED.value
    assert stage.completed_at is not None

    chunk_count = await db_session.scalar(
        select(func.count()).select_from(DocumentChunk).where(DocumentChunk.job_id == job.id)
    )
    assert chunk_count == len(sources) * MOCK_CHUNKS_PER_SOURCE

    processed = ProcessedEventRepository(db_session)
    record = await processed.get_by_event_id(str(inbound.event_id))
    assert record is not None
    assert record.worker_name == WORKER_NAME_EMBEDDING


async def test_process_ingestion_completed_skips_duplicate_event(db_session: AsyncSession) -> None:
    job, _, sources = await _seed_job_with_sources(db_session)
    mock_publisher = AsyncMock(spec=EventPublisher)
    inbound = build_ingestion_completed_event(
        job_id=job.id,
        correlation_id=job.correlation_id,
        source_ids=[source.id for source in sources],
    )

    await process_ingestion_completed(db_session, mock_publisher, inbound)
    mock_publisher.reset_mock()

    duplicate_result = await process_ingestion_completed(db_session, mock_publisher, inbound)
    assert duplicate_result is None
    mock_publisher.publish.assert_not_awaited()

    chunk_count = await db_session.scalar(
        select(func.count()).select_from(DocumentChunk).where(DocumentChunk.job_id == job.id)
    )
    assert chunk_count == len(sources) * MOCK_CHUNKS_PER_SOURCE


async def test_embedding_worker_deletes_message_on_success() -> None:
    worker = EmbeddingWorker()
    worker._delete_message = MagicMock()
    mock_client = MagicMock()

    event = build_ingestion_completed_event(
        job_id=UUID("11111111-1111-4111-8111-111111111111"),
        correlation_id="corr-worker",
        source_ids=[UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")],
    )
    body = json.dumps({"detail": json.loads(event.model_dump_json())})
    mock_client.receive_message.return_value = {
        "Messages": [{"ReceiptHandle": "rh-1", "Body": body, "MessageId": "m-1"}]
    }
    worker._client = mock_client
    worker._queue_url = "http://localstack/000000000000/eventforge-embedding"

    with patch.object(worker, "handle_message", new=AsyncMock()):
        handled = await worker.poll_once()

    assert handled == 1
    worker._delete_message.assert_called_once_with("rh-1")


def test_parse_eventbridge_sqs_body_extracts_ingestion_completed_detail() -> None:
    event = build_ingestion_completed_event(
        job_id=UUID("11111111-1111-4111-8111-111111111111"),
        correlation_id="corr-abc",
        source_ids=[UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")],
    )
    body = json.dumps(
        {
            "version": "0",
            "detail-type": "eventforge.ingestion.completed",
            "source": "eventforge.workers.ingestion",
            "detail": json.loads(event.model_dump_json()),
        }
    )

    detail = parse_eventbridge_sqs_body(body)
    assert detail["detail_type"] == "eventforge.ingestion.completed"
    assert detail["payload"]["source_count"] == 1


def test_build_embedding_completed_event_sets_payload() -> None:
    chunk_ids = [
        UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
        UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
    ]
    event = build_embedding_completed_event(
        job_id=UUID("11111111-1111-4111-8111-111111111111"),
        correlation_id="corr-out",
        chunk_ids=chunk_ids,
    )
    assert event.detail_type == "eventforge.embedding.completed"
    assert event.payload.chunk_count == 2
    assert event.payload.chunk_ids == chunk_ids
