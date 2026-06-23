import uuid

from eventforge.db.models import Job, KnowledgeEntity
from eventforge.services.knowledge.entity_extraction import (
    ExtractedEntityItem,
    build_knowledge_entities,
)
from eventforge.services.knowledge.research_entities import (
    expected_research_task_count,
    research_entities_for_fanout,
)


def _job() -> Job:
    return Job(topic="Quantum computing trends")


def test_research_entities_for_fanout_prefers_concepts() -> None:
    job_id = uuid.uuid4()
    entities = [
        KnowledgeEntity(
            job_id=job_id, name="topic", entity_type="topic"),
        KnowledgeEntity(
            job_id=job_id, name="qubits", entity_type="concept"),
        KnowledgeEntity(
            job_id=job_id, name="entanglement",
            entity_type="concept"),]
    fanout = research_entities_for_fanout(entities)
    assert len(fanout) == 2
    assert {entity.name for entity in fanout} == {"qubits", "entanglement"}


def test_research_entities_for_fanout_uses_topic_when_no_concepts() -> None:
    job_id = uuid.uuid4()
    entities = [
        KnowledgeEntity(
            job_id=job_id, name="only topic", entity_type="topic")]
    fanout = research_entities_for_fanout(entities)
    assert len(fanout) == 1
    assert fanout[0].entity_type == "topic"


def test_expected_research_task_count_matches_fanout() -> None:
    job_id = uuid.uuid4()
    entities = [
        KnowledgeEntity(job_id=job_id, name="topic", entity_type="topic"),
        KnowledgeEntity(job_id=job_id, name="alpha", entity_type="concept"),
    ]
    assert expected_research_task_count(entities) == 1


def test_build_knowledge_entities_skips_duplicate_topic() -> None:
    job = _job()
    items = [
        ExtractedEntityItem(
            name=job.topic,
            entity_type="topic",
            source_chunk_index=None,
        ),
        ExtractedEntityItem(
            name="superconducting qubits",
            entity_type="concept",
            source_chunk_index=0,
        ),
    ]
    entities = build_knowledge_entities(job, [], items, max_entities=10)
    assert len(entities) == 2
    assert entities[0].entity_type == "topic"
    assert entities[1].name == "superconducting qubits"
