from typing import Protocol

from eventforge.services.llm.types import LLMCompletionResult, LLMMessage


class LLMProvider(Protocol):
    """Provider-specific chat completion adapter."""

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        model: str,
        max_tokens: int | None = None,
    ) -> LLMCompletionResult:
        ...
