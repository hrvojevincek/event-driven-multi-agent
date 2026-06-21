import asyncio
import logging
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from eventforge.core.config import Settings, get_settings
from eventforge.events.schemas import QuerySubmittedEvent

logger = logging.getLogger(__name__)

EVENT_SOURCE = "eventforge.api"
PUBLISHER_WORKER_NAME = "api"
BOTO_CONNECT_TIMEOUT_SECONDS = 5
BOTO_READ_TIMEOUT_SECONDS = 10


class EventPublishError(Exception):
    """Raised when EventBridge PutEvents fails."""


class EventPublisher:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: Any | None = None

    @property
    def client(self) -> Any:
        if self._client is None:
            kwargs: dict[str, Any] = {
                "region_name": self._settings.aws_region,
                "aws_access_key_id": self._settings.aws_access_key_id,
                "aws_secret_access_key": self._settings.aws_secret_access_key,
                "config": Config(
                    connect_timeout=BOTO_CONNECT_TIMEOUT_SECONDS,
                    read_timeout=BOTO_READ_TIMEOUT_SECONDS,
                ),
            }
            if self._settings.aws_endpoint_url:
                kwargs["endpoint_url"] = self._settings.aws_endpoint_url
            self._client = boto3.client("events", **kwargs)
        return self._client

    async def publish_query_submitted(self, event: QuerySubmittedEvent) -> None:
        await asyncio.to_thread(self._publish_query_submitted_sync, event)

    def _publish_query_submitted_sync(self, event: QuerySubmittedEvent) -> None:
        try:
            response = self.client.put_events(
                Entries=[
                    {
                        "Source": EVENT_SOURCE,
                        "DetailType": event.detail_type,
                        "Detail": event.model_dump_json(),
                        "EventBusName": self._settings.event_bus_name,
                    }
                ]
            )
        except (BotoCoreError, ClientError) as exc:
            logger.exception(
                "EventBridge publish failed",
                extra={"event_id": str(event.event_id), "job_id": str(event.job_id)},
            )
            raise EventPublishError(str(exc)) from exc

        failed = response.get("FailedEntryCount", 0)
        if failed:
            entry = response.get("Entries", [{}])[0]
            error_code = entry.get("ErrorCode", "Unknown")
            error_message = entry.get("ErrorMessage", "PutEvents failed")
            raise EventPublishError(f"{error_code}: {error_message}")

        logger.info(
            "Published query.submitted",
            extra={
                "event_id": str(event.event_id),
                "correlation_id": event.correlation_id,
                "job_id": str(event.job_id),
            },
        )
