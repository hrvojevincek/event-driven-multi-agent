import json
import logging
import re

from eventforge.db.models import Job, KnowledgeEntity
from eventforge.events.schemas.constants import WORKER_NAME_RESEARCH
from eventforge.services.llm.client import LLMClient
from eventforge.services.llm.types import LLMMessage

logger = logging.getLogger(__name__)

_SUB_QUERY_SYSTEM = (
    "You generate focused research sub-queries for parallel investigation. "
    "Respond with a JSON array of strings only — no markdown fences or commentary. "
    "Return exactly one sub-query per entity, in the same order as listed. "
    "Each sub-query must be a specific, answerable question connecting that entity to the topic."
)


def fallback_sub_query(job: Job, entity: KnowledgeEntity) -> str:
    """Template sub-query used when LLM generation fails."""
    return f"How does {entity.name} relate to {job.topic[:120]}?"


def _build_sub_query_prompt(job: Job, entities: list[KnowledgeEntity]) -> str:
    lines = [
        f"Research topic: {job.topic}",
        "",
        "Entities (generate one sub-query per row, same order):",
    ]
    for index, entity in enumerate(entities):
        lines.append(f"{index + 1}. {entity.name} ({entity.entity_type})")
    lines.append("")
    lines.append(
        "Each sub-query should deepen understanding of that entity within the topic."
    )
    return "\n".join(lines)


def _parse_sub_queries_json(content: str, entity_count: int) -> list[str] | None:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)

    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, list):
        return None

    queries: list[str] = []
    for item in data:
        if not isinstance(item, str) or not item.strip():
            return None
        queries.append(item.strip())

    if len(queries) != entity_count:
        return None

    return queries


async def generate_sub_queries(
    llm_client: LLMClient,
    job: Job,
    entities: list[KnowledgeEntity],
) -> list[str]:
    """Generate one focused research sub-query per entity via LLM."""
    if not entities:
        return []

    prompt = _build_sub_query_prompt(job, entities)
    result = await llm_client.complete(
        [
            LLMMessage(role="system", content=_SUB_QUERY_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ],
        job_id=job.id,
        agent_name=WORKER_NAME_RESEARCH,
    )

    parsed = _parse_sub_queries_json(result.content, len(entities))
    if parsed is not None:
        return parsed

    logger.warning(
        "Sub-query JSON parse failed; falling back to template sub-queries",
        extra={"job_id": str(job.id), "entity_count": len(entities)},
    )
    return [fallback_sub_query(job, entity) for entity in entities]
