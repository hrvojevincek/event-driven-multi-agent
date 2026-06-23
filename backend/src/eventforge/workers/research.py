import asyncio
import logging
from typing import Any

from eventforge.agents.research import (
    parse_knowledge_mined_event,
    parse_research_task_dispatched_event,
    process_knowledge_mined,
    process_research_task_dispatched,
)
from eventforge.core.config import get_settings
from eventforge.core.logging import setup_logging
from eventforge.db.session import get_session_factory
from eventforge.events.parser import parse_eventbridge_sqs_body
from eventforge.events.publisher import EventPublisher
from eventforge.events.schemas.constants import (
    DETAIL_TYPE_KNOWLEDGE_MINED,
    DETAIL_TYPE_RESEARCH_TASK_DISPATCHED,
)
from eventforge.workers.base import SqsConsumer
from eventforge.workers.cost_cap import run_with_cost_cap_handling

logger = logging.getLogger(__name__)


class ResearchWorker(SqsConsumer):
    """Consumes knowledge.mined and research.task.dispatched events."""

    def __init__(self) -> None:
        settings = get_settings()
        super().__init__(settings.research_queue_name, settings)
        self._publisher = EventPublisher(settings)
        self._session_factory = get_session_factory(settings)

    async def handle_message(self, message: dict[str, Any]) -> None:
        detail = parse_eventbridge_sqs_body(message["Body"])
        detail_type = detail.get("detail_type")

        if detail_type == DETAIL_TYPE_KNOWLEDGE_MINED:
            await self._handle_knowledge_mined(detail)
            return

        if detail_type == DETAIL_TYPE_RESEARCH_TASK_DISPATCHED:
            await self._handle_research_task_dispatched(detail)
            return

        msg = f"Unexpected detail_type for research worker: {detail_type}"
        raise ValueError(msg)

    async def _handle_knowledge_mined(self, detail: dict[str, Any]) -> None:
        event = parse_knowledge_mined_event(detail)

        async def _process():
            async with self._session_factory() as session:
                return await process_knowledge_mined(session, self._publisher, event)

        result = await run_with_cost_cap_handling(
            self._session_factory,
            self._publisher,
            detail,
            _process,
        )

        if result is None:
            logger.info(
                "Skipped duplicate knowledge.mined fan-out",
                extra={
                    "event_id": str(event.event_id),
                    "job_id": str(event.job_id),
                    "correlation_id": event.correlation_id,
                },
            )
            return

        logger.info(
            "Research tasks dispatched",
            extra={
                "event_id": str(event.event_id),
                "job_id": str(event.job_id),
                "correlation_id": event.correlation_id,
                "task_count": len(result),
            },
        )

    async def _handle_research_task_dispatched(
            self, detail: dict[str, Any]) -> None:
        event = parse_research_task_dispatched_event(detail)

        async def _process():
            async with self._session_factory() as session:
                return await process_research_task_dispatched(session, self._publisher, event)

        result = await run_with_cost_cap_handling(
            self._session_factory,
            self._publisher,
            detail,
            _process,
        )

        if result is None:
            logger.info(
                "Skipped duplicate research.task.dispatched",
                extra={
                    "event_id": str(event.event_id),
                    "job_id": str(event.job_id),
                    "correlation_id": event.correlation_id,
                    "task_index": event.payload.task_index,
                },
            )
            return

        logger.info(
            "Research task completed",
            extra={
                "event_id": str(event.event_id),
                "job_id": str(event.job_id),
                "correlation_id": event.correlation_id,
                "task_index": result.payload.task_index,
                "note_id": str(result.payload.note_id),
            },
        )


async def main() -> None:
    settings = get_settings()
    setup_logging(settings)
    worker = ResearchWorker()
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
