from eventforge.db.models import JobStageName
from eventforge.events.schemas.constants import (
    DETAIL_TYPE_EMBEDDING_COMPLETED,
    DETAIL_TYPE_INGESTION_COMPLETED,
    DETAIL_TYPE_KNOWLEDGE_MINED,
    DETAIL_TYPE_QUERY_SUBMITTED,
    DETAIL_TYPE_RESEARCH_TASK_COMPLETED,
    DETAIL_TYPE_RESEARCH_TASK_DISPATCHED,
)

DETAIL_TYPE_TO_FAILED_STAGE: dict[str, str] = {
    DETAIL_TYPE_QUERY_SUBMITTED: JobStageName.INGESTION.value,
    DETAIL_TYPE_INGESTION_COMPLETED: JobStageName.EMBEDDING.value,
    DETAIL_TYPE_EMBEDDING_COMPLETED: JobStageName.KNOWLEDGE_MINING.value,
    DETAIL_TYPE_KNOWLEDGE_MINED: JobStageName.RESEARCH.value,
    DETAIL_TYPE_RESEARCH_TASK_DISPATCHED: JobStageName.RESEARCH.value,
    DETAIL_TYPE_RESEARCH_TASK_COMPLETED: JobStageName.SYNTHESIS.value,
}

DETAIL_TYPE_TO_SOURCE_QUEUE: dict[str, str] = {
    DETAIL_TYPE_QUERY_SUBMITTED: "eventforge-ingestion",
    DETAIL_TYPE_INGESTION_COMPLETED: "eventforge-embedding",
    DETAIL_TYPE_EMBEDDING_COMPLETED: "eventforge-knowledge-mining",
    DETAIL_TYPE_KNOWLEDGE_MINED: "eventforge-research",
    DETAIL_TYPE_RESEARCH_TASK_DISPATCHED: "eventforge-research",
    DETAIL_TYPE_RESEARCH_TASK_COMPLETED: "eventforge-synthesis",
}


def stage_for_failed_detail_type(detail_type: str) -> str | None:
    """Map an inbound event detail_type to the worker stage that failed to process it."""
    return DETAIL_TYPE_TO_FAILED_STAGE.get(detail_type)


def source_queue_for_detail_type(detail_type: str) -> str | None:
    """Infer the worker queue an inbound event was consumed from."""
    return DETAIL_TYPE_TO_SOURCE_QUEUE.get(detail_type)
