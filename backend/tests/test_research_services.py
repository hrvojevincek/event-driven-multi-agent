import json

from eventforge.db.models import Job, KnowledgeEntity
from eventforge.services.research.sub_query import (
    _parse_sub_queries_json,
    fallback_sub_query,
)


def _job() -> Job:
    return Job(topic="Quantum computing trends")


def test_fallback_sub_query_templates_entity_and_topic() -> None:
    job = _job()
    entity = KnowledgeEntity(name="superconducting qubits", entity_type="concept")
    query = fallback_sub_query(job, entity)
    assert "superconducting qubits" in query
    assert job.topic in query


def test_parse_sub_queries_json_accepts_fenced_array() -> None:
    raw = '```json\n["Q1?", "Q2?"]\n```'
    assert _parse_sub_queries_json(raw, 2) == ["Q1?", "Q2?"]


def test_parse_sub_queries_json_rejects_wrong_length() -> None:
    assert _parse_sub_queries_json(json.dumps(["only one"]), 2) is None


def test_parse_sub_queries_json_rejects_non_strings() -> None:
    assert _parse_sub_queries_json(json.dumps([{"q": "bad"}]), 1) is None
