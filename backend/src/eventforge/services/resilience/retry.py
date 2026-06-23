import asyncio
import logging
from collections.abc import Awaitable, Callable

from eventforge.core.config import Settings

logger = logging.getLogger(__name__)

async def retry_with_backoff[T](
    operation: Callable[[], Awaitable[T]],
    *,
    settings: Settings,
    is_retryable: Callable[[BaseException], bool],
) -> T:
    """Run an async operation with exponential backoff retries."""
    max_retries = settings.llm_max_retries
    last_error: BaseException | None = None

    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except BaseException as exc:
            if not is_retryable(exc) or attempt >= max_retries:
                raise
            last_error = exc
            delay = min(
                settings.llm_retry_base_delay_seconds * (2**attempt),
                settings.llm_retry_max_delay_seconds,
            )
            logger.warning(
                "Retrying external call after failure",
                extra={
                    "attempt": attempt + 1,
                    "max_retries": max_retries,
                    "delay_seconds": delay,
                    "error": str(exc),
                },
            )
            await asyncio.sleep(delay)

    if last_error is not None:
        raise last_error
    msg = "retry_with_backoff exhausted without result"
    raise RuntimeError(msg)
