from collections.abc import Awaitable, Callable

from eventforge.core.config import Settings
from eventforge.services.resilience.circuit_breaker import get_circuit_breaker
from eventforge.services.resilience.retry import retry_with_backoff


async def call_with_resilience[T](
    breaker_key: str,
    operation: Callable[[], Awaitable[T]],
    *,
    settings: Settings,
    is_retryable: Callable[[BaseException], bool],
) -> T:
    """Execute an external call behind a circuit breaker with retry backoff."""
    breaker = get_circuit_breaker(breaker_key, settings)

    async def _guarded() -> T:
        return await retry_with_backoff(
            operation,
            settings=settings,
            is_retryable=is_retryable,
        )

    return await breaker.call(_guarded)
