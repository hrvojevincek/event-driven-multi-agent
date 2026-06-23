from openai import AsyncOpenAI

from eventforge.core.config import Settings
from eventforge.services.llm.types import LLMCompletionResult, LLMMessage


class OpenAIProvider:
    """Chat completions via the OpenAI API."""

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            msg = "OPENAI_API_KEY is not configured"
            raise ValueError(msg)
        self._settings = settings
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        model: str,
    ) -> LLMCompletionResult:
        response = await self._client.chat.completions.create(
            model=model,
            messages=[{"role": message.role, "content": message.content} for message in messages],
        )
        choice = response.choices[0]
        content = choice.message.content or ""
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        resolved_model = response.model or model
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
