import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from eventforge.core.config import Settings
from eventforge.db.repositories import LLMUsageRepository
from eventforge.events.publisher import EventPublisher
from eventforge.events.schemas.envelope import EventEnvelope
from eventforge.services.pipeline_failure import process_pipeline_failure


class JobCostCapExceededError(Exception):
    """Raised when a job exceeds its configured LLM cost cap."""

    def __init__(
        self,
        job_id: uuid.UUID,
        *,
        total_cost_usd: Decimal,
        cap_usd: Decimal,
    ) -> None:
        self.job_id = job_id
        self.total_cost_usd = total_cost_usd
        self.cap_usd = cap_usd
        super().__init__(
            f"Job {job_id} LLM cost ${total_cost_usd} reached cap ${cap_usd}"
        )


async def assert_job_under_cost_cap(
    session: AsyncSession,
    job_id: uuid.UUID,
    settings: Settings,
) -> None:
    """Raise JobCostCapExceededError when job LLM spend is at or above the cap."""
    cap = settings.job_max_cost_usd
    if cap is None:
        return

    total = await LLMUsageRepository(session).total_cost_by_job_id(job_id)
    if total >= cap:
        raise JobCostCapExceededError(
            job_id,
            total_cost_usd=total,
            cap_usd=cap,
        )


async def emit_cost_cap_pipeline_failure(
    session: AsyncSession,
    publisher: EventPublisher,
    failed_event_detail: dict,
    exc: JobCostCapExceededError,
) -> None:
    """Mark the job failed and emit pipeline.failed for a cost-cap breach."""
    failed_event = EventEnvelope.model_validate(failed_event_detail)
    error_message = (
        f"Job LLM cost cap exceeded: ${exc.total_cost_usd:.6f} >= ${exc.cap_usd:.6f}"
    )
    await process_pipeline_failure(
        session,
        publisher,
        failed_event=failed_event,
        error_message=error_message,
    )
