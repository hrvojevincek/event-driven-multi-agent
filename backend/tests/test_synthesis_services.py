import uuid

from eventforge.db.models import Job, ResearchNote, Source
from eventforge.services.synthesis.report_generation import build_synthesis_prompt


def test_build_synthesis_prompt_includes_sources_and_notes() -> None:
    job = Job(topic="Event-driven patterns")
    sources = [
        Source(
            job_id=uuid.uuid4(),
            url="https://example.com/ed",
            title="Event-Driven 101",
            snippet="Events decouple producers and consumers.",
        )
    ]
    notes = [
        ResearchNote(
            job_id=job.id,
            task_id=uuid.uuid4(),
            task_index=0,
            sub_query="How do events improve scalability?",
            content="Fan-out via queues improves throughput [RAG-0].",
        )
    ]

    prompt = build_synthesis_prompt(job, notes, sources)

    assert job.topic in prompt
    assert "[SRC-0]" in prompt
    assert "Event-Driven 101" in prompt
    assert "How do events improve scalability?" in prompt
    assert "Fan-out via queues" in prompt
