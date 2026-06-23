import logging
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

from eventforge.core.config import Settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitBreakerOpenError(Exception):
    """Raised when a circuit breaker is open and calls are rejected."""

    def __init__(self, breaker_name: str) -> None:
        self.breaker_name = breaker_name
        super().__init__(f"Circuit breaker open: {breaker_name}")


class CircuitBreaker:
    """In-memory circuit breaker with closed, open, and half-open states."""

    def __init__(
        self,
        name: str,
        *,
        failure_threshold: int,
        recovery_timeout_seconds: float,
    ) -> None:
        self.name = name
        self._failure_threshold = failure_threshold
        self._recovery_timeout_seconds = recovery_timeout_seconds
        self._failure_count = 0
        self._opened_at: float | None = None
        self._half_open = False

    async def call(self, operation: Callable[[], Awaitable[T]]) -> T:
        if self._is_open():
            raise CircuitBreakerOpenError(self.name)

        try:
            result = await operation()
        except Exception:
            self._record_failure()
            raise

        self._record_success()
        return result

    def _is_open(self) -> bool:
        if self._opened_at is None:
            return False

        elapsed = time.monotonic() - self._opened_at
        if elapsed >= self._recovery_timeout_seconds:
            self._half_open = True
            logger.info(
                "Circuit breaker half-open",
                extra={"breaker": self.name},
            )
            return False

        return True

    def _record_success(self) -> None:
        if self._half_open or self._failure_count > 0:
            logger.info(
                "Circuit breaker closed",
                extra={"breaker": self.name},
            )
        self._failure_count = 0
        self._opened_at = None
        self._half_open = False

    def _record_failure(self) -> None:
        if self._half_open:
            self._open_breaker()
            return

        self._failure_count += 1
        if self._failure_count >= self._failure_threshold:
            self._open_breaker()

    def _open_breaker(self) -> None:
        self._opened_at = time.monotonic()
        self._half_open = False
        logger.warning(
            "Circuit breaker opened",
            extra={"breaker": self.name, "failure_threshold": self._failure_threshold},
        )


_registry: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, settings: Settings) -> CircuitBreaker:
    """Return a process-wide circuit breaker for the given provider key."""
    if name not in _registry:
        _registry[name] = CircuitBreaker(
            name,
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_timeout_seconds=settings.circuit_breaker_recovery_timeout_seconds,
        )
    return _registry[name]


def reset_circuit_breakers() -> None:
    """Clear all circuit breakers (for tests)."""
    _registry.clear()
