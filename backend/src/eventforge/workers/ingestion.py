import asyncio
import logging
from typing import Any

from eventforge.agents.ingestion import parse_query_submitted_event, process_query_submitted
from eventforge.core.config import get_settings
from eventforge.core.logging import setup_logging
from eventforge.db.session import get_session_factory
from eventforge.events.parser import parse_eventbridge_sqs_body
from eventforge.events.publisher import EventPublisher
from eventforge.workers.base import SqsConsumer

logger = logging.getLogger(__name__)


class IngestionWorker(SqsConsumer):
    def __init__(self) -> None:
        settings = get_settings()
        super().__init__(settings.ingestion_queue_name, settings)
        self._publisher = EventPublisher(settings)
        self._session_factory = get_session_factory(settings)

    async def handle_message(self, message: dict[str, Any]) -> None:
        detail = parse_eventbridge_sqs_body(message["Body"])
        event = parse_query_submitted_event(detail)

        async with self._session_factory() as session:
            result = await process_query_submitted(session, self._publisher, event)

        if result is None:
            logger.info(
                "Skipped duplicate query.submitted",
                extra={
                    "event_id": str(event.event_id),
                    "job_id": str(event.job_id),
                    "correlation_id": event.correlation_id,
                },
            )
            return

        logger.info(
            "Ingestion completed",
            extra={
                "event_id": str(event.event_id),
                "job_id": str(event.job_id),
                "correlation_id": event.correlation_id,
                "source_count": result.payload.source_count,
            },
        )


async def main() -> None:
    settings = get_settings()
    setup_logging(settings)
    worker = IngestionWorker()
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
