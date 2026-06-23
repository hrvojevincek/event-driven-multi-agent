from eventforge.db.models import Job, ResearchNote, Source
from eventforge.events.schemas.constants import WORKER_NAME_SYNTHESIS
from eventforge.services.llm.client import LLMClient
from eventforge.services.llm.types import LLMMessage

_SYNTHESIS_SYSTEM = (
    "You are a senior research editor producing a final cited synthesis report. "
    "Write structured markdown with sections: Executive summary, Key findings, "
    "Analysis, Conclusion, and References. "
    "Cite ingested sources inline as [SRC-n] using the source catalog below. "
    "Integrate all parallel research notes; resolve overlaps and contradictions. "
    "Stay grounded in the provided notes and sources; do not invent citations."
)


def build_synthesis_prompt(
    job: Job,
    notes: list[ResearchNote],
    sources: list[Source],
) -> str:
    """Assemble the user prompt for final report generation."""
    lines = [
        f"Research topic: {job.topic}",
        "",
        "Source catalog (cite inline as [SRC-n]):",
    ]

    if sources:
        for index, source in enumerate(sources):
            lines.extend(
                [
                    f"[SRC-{index}] {source.title}",
                    f"URL: {source.url}",
                    source.snippet[:2000],
                    "",
                ]
            )
    else:
        lines.append("(No ingested sources available.)")
        lines.append("")

    lines.append("Parallel research notes:")
    if notes:
        for note in notes:
            lines.extend(
                [
                    f"--- Note {note.task_index + 1} ---",
                    f"Sub-query: {note.sub_query}",
                    note.content,
                    "",
                ]
            )
    else:
        lines.append("(No research notes available.)")
        lines.append("")

    lines.append(
        "Produce a cohesive final synthesis that answers the research topic, "
        "with inline [SRC-n] citations and a References section listing cited sources."
    )
    return "\n".join(lines)


async def generate_synthesis_report(
    llm_client: LLMClient,
    job: Job,
    notes: list[ResearchNote],
    sources: list[Source],
) -> str:
    """Generate cited markdown synthesis from research notes and ingested sources."""
    prompt = build_synthesis_prompt(job, notes, sources)
    result = await llm_client.complete(
        [
            LLMMessage(role="system", content=_SYNTHESIS_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ],
        job_id=job.id,
        agent_name=WORKER_NAME_SYNTHESIS,
    )
    return result.content.strip()
