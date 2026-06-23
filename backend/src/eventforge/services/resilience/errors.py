import httpx
from anthropic import (
    APIConnectionError as AnthropicAPIConnectionError,
)
from anthropic import (
    InternalServerError as AnthropicInternalServerError,
)
from anthropic import (
    RateLimitError as AnthropicRateLimitError,
)
from openai import (
    APIConnectionError as OpenAIAPIConnectionError,
)
from openai import (
    APITimeoutError,
)
from openai import (
    InternalServerError as OpenAIInternalServerError,
)
from openai import (
    RateLimitError as OpenAIRateLimitError,
)


def is_retryable_openai_error(exc: BaseException) -> bool:
    """Return True for transient OpenAI SDK failures."""
    return isinstance(
        exc,
        (
            OpenAIAPIConnectionError,
            APITimeoutError,
            OpenAIRateLimitError,
            OpenAIInternalServerError,
        ),
    )


def is_retryable_anthropic_error(exc: BaseException) -> bool:
    """Return True for transient Anthropic SDK failures."""
    return isinstance(
        exc,
        (
            AnthropicAPIConnectionError,
            AnthropicRateLimitError,
            AnthropicInternalServerError,
        ),
    )


def is_retryable_httpx_error(exc: BaseException) -> bool:
    """Return True for transient HTTP client failures (e.g. Tavily)."""
    if isinstance(exc, httpx.TimeoutException | httpx.ConnectError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {429, 500, 502, 503, 504}
    return False
