from uuid import NAMESPACE_URL, UUID, uuid5


def deterministic_event_id(job_id: UUID, detail_type: str) -> UUID:
    """Stable event_id for stage output events so retries publish the same envelope."""
    return uuid5(NAMESPACE_URL, f"{job_id}:{detail_type}")
