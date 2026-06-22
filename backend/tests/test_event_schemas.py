import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from eventforge.events.schemas import (
    DETAIL_TYPE_QUERY_SUBMITTED,
    QUERY_SUBMITTED_SCHEMA_VERSION,
    QueryDepth,
    QuerySubmittedEvent,
    QuerySubmittedPayload,
    build_query_submitted_event,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_EVENTS = REPO_ROOT / "shared" / "events"


def test_query_submitted_payload_requires_topic() -> None:
    with pytest.raises(ValidationError):
        QuerySubmittedPayload.model_validate({})


def test_query_submitted_payload_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        QuerySubmittedPayload.model_validate({"topic": "AI agents", "extra": True})


def test_build_query_submitted_event_sets_envelope_fields() -> None:
    job_id = UUID("11111111-1111-4111-8111-111111111111")
    event = build_query_submitted_event(
        job_id=job_id,
        correlation_id="corr-abc",
        topic="Event-driven architectures",
        depth=QueryDepth.DEEP,
        max_sources=10,
        event_id=UUID("22222222-2222-4222-8222-222222222222"),
        timestamp=datetime(2026, 6, 21, 12, 0, tzinfo=UTC),
    )

    assert event.detail_type == DETAIL_TYPE_QUERY_SUBMITTED
    assert event.schema_version == QUERY_SUBMITTED_SCHEMA_VERSION
    assert event.job_id == job_id
    assert event.payload.topic == "Event-driven architectures"
    assert event.payload.depth == QueryDepth.DEEP
    assert event.payload.max_sources == 10


def test_query_submitted_event_serializes_to_json_compatible_dict() -> None:
    event = build_query_submitted_event(
        job_id=UUID("11111111-1111-4111-8111-111111111111"),
        correlation_id="corr-abc",
        topic="Test",
    )

    data = json.loads(event.model_dump_json())
    assert data["detail_type"] == "eventforge.query.submitted"
    assert data["payload"]["topic"] == "Test"
    assert data["payload"]["depth"] == "standard"


def test_round_trip_through_pydantic() -> None:
    original = build_query_submitted_event(
        job_id=UUID("11111111-1111-4111-8111-111111111111"),
        correlation_id="corr-abc",
        topic="Round trip",
    )

    restored = QuerySubmittedEvent.model_validate_json(original.model_dump_json())
    assert restored == original


@pytest.mark.parametrize(
    "filename",
    [
        "envelope.schema.json",
        "query.submitted.schema.json",
        "ingestion.completed.schema.json",
        "embedding.completed.schema.json",
    ],
)
def test_json_schema_files_are_valid_json(filename: str) -> None:
    path = SHARED_EVENTS / filename
    assert path.exists(), f"missing schema file: {path}"
    json.loads(path.read_text())
