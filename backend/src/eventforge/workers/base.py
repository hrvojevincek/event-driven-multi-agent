import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from eventforge.core.aws import boto_client
from eventforge.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class SqsConsumer(ABC):
    """Long-poll an SQS queue and dispatch messages to handle_message."""

    def __init__(
        self,
        queue_name: str,
        settings: Settings | None = None,
        *,
        wait_time_seconds: int | None = None,
        max_messages: int | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._queue_name = queue_name
        self._wait_time_seconds = wait_time_seconds or self._settings.sqs_wait_time_seconds
        self._max_messages = max_messages or self._settings.sqs_max_messages
        self._client: Any | None = None
        self._queue_url: str | None = None

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = boto_client("sqs", self._settings)
        return self._client

    @property
    def queue_url(self) -> str:
        if self._queue_url is None:
            response = self.client.get_queue_url(QueueName=self._queue_name)
            self._queue_url = response["QueueUrl"]
        return self._queue_url

    async def run_forever(self) -> None:
        logger.info("Starting SQS consumer", extra={"queue": self._queue_name})
        while True:
            await self.poll_once()

    async def poll_once(self) -> int:
        messages = await asyncio.to_thread(self._receive_messages)
        for message in messages:
            receipt_handle = message["ReceiptHandle"]
            try:
                await self.handle_message(message)
            except Exception:
                logger.exception(
                    "Message handler failed; leaving on queue for retry",
                    extra={"message_id": message.get("MessageId")},
                )
                continue

            await asyncio.to_thread(self._delete_message, receipt_handle)
        return len(messages)

    def _receive_messages(self) -> list[dict[str, Any]]:
        try:
            response = self.client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=self._max_messages,
                WaitTimeSeconds=self._wait_time_seconds,
                MessageAttributeNames=["All"],
            )
        except (BotoCoreError, ClientError) as exc:
            logger.exception("SQS receive failed", extra={"queue": self._queue_name})
            raise exc
        return response.get("Messages", [])

    def _delete_message(self, receipt_handle: str) -> None:
        self.client.delete_message(QueueUrl=self.queue_url, ReceiptHandle=receipt_handle)

    @abstractmethod
    async def handle_message(self, message: dict[str, Any]) -> None:
        """Process one SQS message. Raise to leave the message for retry."""
