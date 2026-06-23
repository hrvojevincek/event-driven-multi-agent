import logging

from anthropic import AsyncAnthropic

from eventforge.core.config import Settings
from eventforge.services.llm.types import LLMCompletionResult, LLMMessage

logger = logging.getLogger(__name__)


class AnthropicProvider:
    """Chat completions via the Anthropic API."""

    def __init__(self, settings: Settings) -> None:
        if not settings.anthropic_api_key:
            msg = "ANTHROPIC_API_KEY is not configured"
            raise ValueError(msg)
        self._settings = settings
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        model: str,
        max_tokens: int | None = None,
    ) -> LLMCompletionResult:
        system_prompt: str | None = None
        anthropic_messages: list[dict[str, str]] = []
        for message in messages:
            if message.role == "system":
                if system_prompt is not None:
                    msg = "Anthropic provider supports at most one system message"
                    raise ValueError(msg)
                system_prompt = message.content
                continue
            anthropic_messages.append({"role": message.role, "content": message.content})

        resolved_max_tokens = max_tokens or self._settings.llm_max_output_tokens
        kwargs: dict = {
            "model": model,
            "max_tokens": resolved_max_tokens,
            "messages": anthropic_messages,
        }
        if system_prompt is not None:
            kwargs["system"] = system_prompt

        response = await self._client.messages.create(**kwargs)
        content = "".join(
            block.text for block in response.content if block.type == "text"
        )
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        resolved_model = response.model
        cost_usd = self._settings.total_cost_for_tokens(
            resolved_model,
            input_tokens,
            output_tokens,
        )
        return LLMCompletionResult(
            content=content,
            model=resolved_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )
