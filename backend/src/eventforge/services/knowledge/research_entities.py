from eventforge.db.models import KnowledgeEntity


def research_entities_for_fanout(entities: list[KnowledgeEntity]) -> list[KnowledgeEntity]:
    """Return entities that each receive one parallel research sub-task."""
    concepts = [entity for entity in entities if entity.entity_type != "topic"]
    return concepts if concepts else list(entities)


def expected_research_task_count(entities: list[KnowledgeEntity]) -> int:
    """Number of research notes required before synthesis can run."""
    return len(research_entities_for_fanout(entities))
