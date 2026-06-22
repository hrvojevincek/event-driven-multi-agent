import asyncio
import logging
from typing import Any

from eventforge.agents.knowledge import parse_embedding_completed_event, process_embedding_completed
from eventforge.core.config import get_settings
from eventforge.core.logging import setup_logging
from eventforge.db.session import get_session_factory
from eventforge.events.parser import parse_eventbridge_sqs_body
from eventforge.events.publisher import EventPublisher
from eventforge.workers.base import SqsConsumer

logger = logging.getLogger(__name__)


class KnowledgeWorker(SqsConsumer):
    def __init__(self) -> None:
        settings = get_settings()
        super().__init__(settings.knowledge_mining_queue_name, settings)
        self._publisher = EventPublisher(settings)
        self._session_factory = get_session_factory(settings)

    async def handle_message(self, message: dict[str, Any]) -> None:
        detail = parse_eventbridge_sqs_body(message["Body"])
        event = parse_embedding_completed_event(detail)

        async with self._session_factory() as session:
            result = await process_embedding_completed(session, self._publisher, event)

        if result is None:
            logger.info(
                "Skipped duplicate embedding.completed",
                extra={
                    "event_id": str(event.event_id),
                    "job_id": str(event.job_id),
                    "correlation_id": event.correlation_id,
                },
            )
            return

        logger.info(
            "Knowledge mining completed",
            extra={
                "event_id": str(event.event_id),
                "job_id": str(event.job_id),
                "correlation_id": event.correlation_id,
                "entity_count": result.payload.entity_count,
            },
        )


async def main() -> None:
    settings = get_settings()
    setup_logging(settings)
    worker = KnowledgeWorker()
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
