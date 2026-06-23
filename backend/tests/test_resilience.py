from decimal import Decimal

import pytest
from pydantic import ValidationError

from eventforge.core.config import Settings
from eventforge.services.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
)


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failure_threshold() -> None:
    breaker = CircuitBreaker("test", failure_threshold=2,
                             recovery_timeout_seconds=60.0)

    async def _fail() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await breaker.call(_fail)
    with pytest.raises(RuntimeError, match="boom"):
        await breaker.call(_fail)
    with pytest.raises(CircuitBreakerOpenError):
        await breaker.call(_fail)


@pytest.mark.asyncio
async def test_retry_with_backoff_retries_transient_errors() -> None:
    from eventforge.services.resilience.retry import retry_with_backoff

    settings = Settings(
        llm_max_retries=3,
        llm_retry_base_delay_seconds=0.01,
        llm_retry_max_delay_seconds=0.05,
    )
    attempts = 0

    async def _flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("transient")
        return "ok"

    result = await retry_with_backoff(
        _flaky,
        settings=settings,
        is_retryable=lambda exc: isinstance(exc, RuntimeError),
    )

    assert result == "ok"
    assert attempts == 3


@pytest.mark.asyncio
async def test_retry_with_backoff_does_not_retry_non_retryable_errors() -> None:
    from eventforge.services.resilience.retry import retry_with_backoff

    settings = Settings(llm_max_retries=3, llm_retry_base_delay_seconds=0.01)
    attempts = 0

    async def _fail() -> None:
        nonlocal attempts
        attempts += 1
        raise ValueError("permanent")

    with pytest.raises(ValueError, match="permanent"):
        await retry_with_backoff(
            _fail,
            settings=settings,
            is_retryable=lambda exc: isinstance(exc, RuntimeError),
        )

    assert attempts == 1


def test_settings_rejects_negative_llm_max_retries() -> None:
    with pytest.raises(ValidationError):
        Settings(llm_max_retries=-1)


def test_settings_rejects_base_delay_exceeding_max_delay() -> None:
    with pytest.raises(ValidationError):
        Settings(
            llm_retry_base_delay_seconds=10.0,
            llm_retry_max_delay_seconds=5.0,
        )


def test_settings_rejects_non_positive_job_max_cost_usd() -> None:
    with pytest.raises(ValidationError):
        Settings(job_max_cost_usd=Decimal("0"))
