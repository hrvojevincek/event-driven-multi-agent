import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from eventforge.core.config import LLMProviderName, Settings, get_settings
from eventforge.db.repositories.llm_usage import LLMUsageRepository
from eventforge.services.llm.providers.anthropic import AnthropicProvider
from eventforge.services.llm.providers.base import LLMProvider
from eventforge.services.llm.providers.openai import OpenAIProvider
from eventforge.services.llm.types import LLMCompletionResult, LLMMessage


class LLMClient:
    """Unified chat completion client with optional usage logging."""

    def __init__(
        self,
        settings: Settings | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._session = session
        self._providers: dict[LLMProviderName, LLMProvider] = {}

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        job_id: uuid.UUID,
        agent_name: str,
        model: str | None = None,
    ) -> LLMCompletionResult:
        resolved_model = model or self._settings.llm_default_model
        provider_name = self._settings.resolve_llm_provider(resolved_model)
        provider = self._get_provider(provider_name)
        result = await provider.complete(messages, model=resolved_model)

        if self._session is not None:
            await LLMUsageRepository(self._session).log(
                job_id=job_id,
                agent_name=agent_name,
                model=result.model,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_usd=result.cost_usd,
            )

        return result

    def _get_provider(self, provider_name: LLMProviderName) -> LLMProvider:
        if provider_name not in self._providers:
            if provider_name == "openai":
                self._providers[provider_name] = OpenAIProvider(self._settings)
            else:
                self._providers[provider_name] = AnthropicProvider(self._settings)
        return self._providers[provider_name]


def get_llm_client(session: AsyncSession | None = None) -> LLMClient:
    """Build an LLM client, optionally bound to a DB session for usage logging."""
    return LLMClient(session=session)
