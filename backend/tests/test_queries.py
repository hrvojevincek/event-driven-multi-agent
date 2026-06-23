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
from eventforge.core.aws import BOTO_CONNECT_TIMEOUT_SECONDS, BOTO_READ_TIMEOUT_SECONDS
from eventforge.core.config import get_settings
from eventforge.db.models import Job, JobStageName, ProcessedEvent, SynthesisReport
from eventforge.db.repositories import JobRepository, ProcessedEventRepository
from eventforge.db.session import reset_engine
from eventforge.events.publisher import (
    EVENT_SOURCE_API,
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
    publisher._publish_sync(event, EVENT_SOURCE_API)

    mock_client.put_events.assert_called_once()
    entry = mock_client.put_events.call_args.kwargs["Entries"][0]
    assert entry["Source"] == EVENT_SOURCE_API
    assert entry["DetailType"] == "eventforge.query.submitted"
    assert entry["EventBusName"] == settings.event_bus_name
    detail = json.loads(entry["Detail"])
    assert detail["payload"]["topic"] == "Publish test"


def test_publisher_client_uses_boto_timeouts() -> None:
    with patch("eventforge.core.aws.boto3.client") as mock_boto_client:
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


async def test_get_query_returns_job_with_stages(client: AsyncClient) -> None:
    create_response = await client.post(
        "/api/v1/queries",
        json={"topic": "GET detail test", "depth": "standard"},
    )
    assert create_response.status_code == 201
    job_id = create_response.json()["job_id"]

    response = await client.get(f"/api/v1/queries/{job_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == job_id
    assert body["topic"] == "GET detail test"
    assert body["depth"] == "standard"
    assert body["status"] == "pending"
    assert body["correlation_id"] == create_response.json()["correlation_id"]
    assert len(body["stages"]) == len(JobStageName)
    assert [stage["stage"] for stage in body["stages"]] == [name.value for name in JobStageName]
    assert all(stage["status"] == "pending" for stage in body["stages"])


async def test_get_query_returns_404_for_unknown_job(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/queries/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


async def test_list_queries_returns_mock_user_jobs(client: AsyncClient) -> None:
    first = await client.post(
        "/api/v1/queries",
        json={"topic": "First list item", "depth": "standard"},
    )
    second = await client.post(
        "/api/v1/queries",
        json={"topic": "Second list item", "depth": "deep"},
    )
    assert first.status_code == 201
    assert second.status_code == 201

    response = await client.get("/api/v1/queries")

    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 2
    assert body[0]["job_id"] == second.json()["job_id"]
    assert body[0]["topic"] == "Second list item"
    assert body[0]["depth"] == "deep"
    assert body[0]["status"] == "pending"
    assert body[1]["job_id"] == first.json()["job_id"]
    assert body[1]["topic"] == "First list item"


async def test_get_query_includes_synthesis_report_when_present(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    create_response = await client.post(
        "/api/v1/queries",
        json={"topic": "Synthesis detail test", "depth": "standard"},
    )
    job_id = UUID(create_response.json()["job_id"])

    db_session.add(
        SynthesisReport(
            job_id=job_id,
            content="# Mock report\n\nFindings here.",
        )
    )
    await db_session.flush()

    response = await client.get(f"/api/v1/queries/{job_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["synthesis_report"] is not None
    assert body["synthesis_report"]["content"] == "# Mock report\n\nFindings here."
    assert UUID(body["synthesis_report"]["id"])


async def test_get_query_synthesis_report_null_when_absent(client: AsyncClient) -> None:
    create_response = await client.post(
        "/api/v1/queries",
        json={"topic": "No synthesis yet", "depth": "standard"},
    )
    job_id = create_response.json()["job_id"]

    response = await client.get(f"/api/v1/queries/{job_id}")

    assert response.status_code == 200
    assert response.json()["synthesis_report"] is None


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
