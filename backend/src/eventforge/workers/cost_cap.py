import logging
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.ext.asyncio import async_sessionmaker

from eventforge.events.publisher import EventPublisher
from eventforge.services.resilience import (
    JobCostCapExceededError,
    emit_cost_cap_pipeline_failure,
)

logger = logging.getLogger(__name__)


async def run_with_cost_cap_handling[T](
    session_factory: async_sessionmaker[Any],
    publisher: EventPublisher,
    detail: dict,
    process: Callable[[], Awaitable[T]],
) -> T | None:
    """Run an agent step; on cost-cap breach emit pipeline.failed and return None."""
    try:
        return await process()
    except JobCostCapExceededError as exc:
        async with session_factory() as session:
            await emit_cost_cap_pipeline_failure(session, publisher, detail, exc)
        logger.warning(
            "Job cost cap exceeded; pipeline marked failed",
            extra={
                "job_id": str(exc.job_id),
                "total_cost_usd": str(exc.total_cost_usd),
                "cap_usd": str(exc.cap_usd),
            },
        )
        return None
