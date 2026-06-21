import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from eventforge.api.deps import get_db
from eventforge.api.routes.queries import get_publisher
from eventforge.core.config import get_settings
from eventforge.db.models import Job, JobStageName, ProcessedEvent
from eventforge.db.repositories import JobRepository, ProcessedEventRepository
from eventforge.db.session import reset_engine
from eventforge.events.publisher import (
    BOTO_CONNECT_TIMEOUT_SECONDS,
    BOTO_READ_TIMEOUT_SECONDS,
    EVENT_SOURCE,
    PUBLISHER_WORKER_NAME,
    EventPublisher,
    EventPublishError,
)
from eventforge.events.schemas import QueryDepth, QuerySubmittedEvent, build_query_submitted_event
from eventforge.main import app
from eventforge.services.query import submit_query

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


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    mock_publisher = AsyncMock(spec=EventPublisher)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_publisher] = lambda: mock_publisher
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.mock_publisher = mock_publisher  # type: ignore[attr-defined]
        yield ac

    app.dependency_overrides.clear()


async def test_submit_query_creates_job_stages_and_publishes(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/queries",
        json={"topic": "Event-driven architectures", "depth": "deep", "max_sources": 5},
    )

    assert response.status_code == 201
    body = response.json()
    assert UUID(body["job_id"])
    assert body["correlation_id"]

    client.mock_publisher.publish_query_submitted.assert_awaited_once()  # type: ignore[attr-defined]
    published_event: QuerySubmittedEvent = (
        client.mock_publisher.publish_query_submitted.await_args.args[0]  # type: ignore[attr-defined]
    )
    assert published_event.payload.topic == "Event-driven architectures"
    assert published_event.payload.depth == QueryDepth.DEEP
    assert published_event.payload.max_sources == 5


async def test_submit_query_requires_topic(client: AsyncClient) -> None:
    response = await client.post("/api/v1/queries", json={"depth": "standard"})
    assert response.status_code == 422


async def test_submit_query_records_processed_event(db_session: AsyncSession) -> None:
    mock_publisher = AsyncMock(spec=EventPublisher)

    result = await submit_query(
        db_session,
        mock_publisher,
        topic="Idempotency test",
        depth=QueryDepth.STANDARD,
    )

    mock_publisher.publish_query_submitted.assert_awaited_once()
    event: QuerySubmittedEvent = mock_publisher.publish_query_submitted.await_args.args[0]

    repo = ProcessedEventRepository(db_session)
    assert await repo.exists(str(event.event_id)) is True

    fetched = await JobRepository(db_session).get_by_id(result.job_id)
    assert fetched is not None
    assert fetched.correlation_id == result.correlation_id
    assert len(fetched.stages) == len(JobStageName)


async def test_submit_query_skips_publish_when_event_already_processed(
    db_session: AsyncSession,
) -> None:
    mock_publisher = AsyncMock(spec=EventPublisher)
    event_id = uuid.uuid4()
    db_session.add(ProcessedEvent(event_id=str(event_id), worker_name=PUBLISHER_WORKER_NAME))
    await db_session.flush()

    fixed_event = build_query_submitted_event(
        job_id=uuid.uuid4(),
        correlation_id=uuid.uuid4().hex,
        topic="Existing",
        event_id=event_id,
    )

    with patch("eventforge.services.query.build_query_submitted_event", return_value=fixed_event):
        await submit_query(db_session, mock_publisher, topic="Existing")

    mock_publisher.publish_query_submitted.assert_not_awaited()


def test_publisher_put_events_payload() -> None:
    event = build_query_submitted_event(
        job_id=UUID("11111111-1111-4111-8111-111111111111"),
        correlation_id="corr-abc",
        topic="Publish test",
    )
    mock_client = MagicMock()
    mock_client.put_events.return_value = {"FailedEntryCount": 0, "Entries": [{}]}

    publisher = EventPublisher(settings)
    publisher._client = mock_client
    publisher._publish_query_submitted_sync(event)

    mock_client.put_events.assert_called_once()
    entry = mock_client.put_events.call_args.kwargs["Entries"][0]
    assert entry["Source"] == EVENT_SOURCE
    assert entry["DetailType"] == "eventforge.query.submitted"
    assert entry["EventBusName"] == settings.event_bus_name
    detail = json.loads(entry["Detail"])
    assert detail["payload"]["topic"] == "Publish test"


def test_publisher_client_uses_boto_timeouts() -> None:
    with patch("eventforge.events.publisher.boto3.client") as mock_boto_client:
        publisher = EventPublisher(settings)
        _ = publisher.client

    mock_boto_client.assert_called_once()
    config = mock_boto_client.call_args.kwargs["config"]
    assert config.connect_timeout == BOTO_CONNECT_TIMEOUT_SECONDS
    assert config.read_timeout == BOTO_READ_TIMEOUT_SECONDS


@pytest.mark.integration
async def test_publisher_reaches_localstack_when_available() -> None:
    import httpx

    try:
        response = httpx.get(f"{settings.aws_endpoint_url}/_localstack/health", timeout=1.0)
        response.raise_for_status()
    except Exception:
        pytest.skip("LocalStack is not running")

    publisher = EventPublisher(settings)
    event = build_query_submitted_event(
        job_id=UUID("33333333-3333-4333-8333-333333333333"),
        correlation_id="integration-corr",
        topic="LocalStack integration",
    )

    await publisher.publish_query_submitted(event)

    mock_client = publisher.client
    assert mock_client is not None


async def test_submit_query_returns_502_when_publish_fails(
    db_session: AsyncSession,
) -> None:
    failing_publisher = AsyncMock(spec=EventPublisher)
    failing_publisher.publish_query_submitted.side_effect = EventPublishError("bus unavailable")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_publisher] = lambda: failing_publisher
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/queries",
            json={"topic": "Should fail publish"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 502
    assert "Failed to publish" in response.json()["detail"]["message"]

    count = await db_session.scalar(
        select(func.count()).select_from(Job).where(Job.topic == "Should fail publish")
    )
    assert count == 0
