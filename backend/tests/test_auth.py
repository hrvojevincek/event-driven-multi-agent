import uuid
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from eventforge.api.deps import get_db
from eventforge.api.routes.queries import get_publisher
from eventforge.core.config import Settings, get_settings
from eventforge.db.models import Job, JobStatus, User
from eventforge.db.repositories import UserRepository
from eventforge.db.session import reset_engine
from eventforge.events.publisher import EventPublisher
from eventforge.main import app


@pytest.fixture
def settings() -> Settings:
    get_settings.cache_clear()
    settings = get_settings()
    yield settings
    get_settings.cache_clear()


@pytest.fixture
async def db_session(settings: Settings) -> AsyncSession:
    reset_engine()
    engine = create_async_engine(
        settings.async_database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()
    reset_engine()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_publisher] = lambda: MagicMock(
        spec=EventPublisher)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


async def test_queries_use_mock_user_without_bearer(
        client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/queries",
        json={"topic": "Open API query", "depth": "standard"},
    )
    assert response.status_code == 201


async def test_get_query_returns_404_for_other_users_job(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner = User(auth_subject_id="other-user-sub", email="owner@example.com")
    db_session.add(owner)
    await db_session.flush()

    job = Job(
        user_id=owner.id,
        correlation_id=uuid.uuid4().hex,
        topic="Private job",
        depth="standard",
        status=JobStatus.PENDING.value,
    )
    db_session.add(job)
    await db_session.flush()

    response = await client.get(f"/api/v1/queries/{job.id}")
    assert response.status_code == 404


async def test_list_queries_scoped_to_mock_user(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    mock_user = await UserRepository(db_session).get_or_create_mock_user()
    other = await UserRepository(db_session).get_or_create_by_auth_subject(
        "other-sub",
        email="other@example.com",
    )

    db_session.add_all(
        [
            Job(
                user_id=mock_user.id,
                correlation_id=uuid.uuid4().hex,
                topic="Mine",
                depth="standard",
                status=JobStatus.PENDING.value,
            ),
            Job(
                user_id=other.id,
                correlation_id=uuid.uuid4().hex,
                topic="Theirs",
                depth="standard",
                status=JobStatus.PENDING.value,
            ),
        ]
    )
    await db_session.flush()

    response = await client.get("/api/v1/queries")
    assert response.status_code == 200
    topics = {item["topic"] for item in response.json()}
    assert "Mine" in topics
    assert "Theirs" not in topics
