from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eventforge.core.config import Settings
from eventforge.core.llm_pricing import DEFAULT_MODEL_PRICING, compute_cost_usd
from eventforge.services.llm.providers.anthropic import AnthropicProvider
from eventforge.services.llm.providers.openai import OpenAIProvider
from eventforge.services.llm.types import LLMMessage


def test_compute_cost_usd_gpt4o_mini() -> None:
    cost = compute_cost_usd(
        "gpt-4o-mini",
        input_tokens=1_000_000,
        output_tokens=500_000,
        pricing_table=DEFAULT_MODEL_PRICING,
    )
    assert cost == Decimal("0.45")


def test_compute_cost_usd_openai_versioned_model_id() -> None:
    exact = compute_cost_usd(
        "gpt-4o-mini",
        input_tokens=7323,
        output_tokens=0,
        pricing_table=DEFAULT_MODEL_PRICING,
    )
    versioned = compute_cost_usd(
        "gpt-4o-mini-2024-07-18",
        input_tokens=7323,
        output_tokens=0,
        pricing_table=DEFAULT_MODEL_PRICING,
    )
    assert versioned == exact
    assert versioned > Decimal("0")


def test_compute_cost_usd_embedding_versioned_model_id() -> None:
    cost = compute_cost_usd(
        "text-embedding-3-small-2024-07-18",
        input_tokens=10_000,
        output_tokens=0,
        pricing_table=DEFAULT_MODEL_PRICING,
    )
    assert cost == Decimal("0.0002")


def test_settings_total_cost_for_tokens_versioned_model() -> None:
    settings = Settings()
    cost = settings.total_cost_for_tokens("gpt-4o-mini-2024-07-18", 1000, 2000)
    expected = settings.total_cost_for_tokens("gpt-4o-mini", 1000, 2000)
    assert cost == expected


def test_compute_cost_usd_unknown_model_returns_zero(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING"):
        cost = compute_cost_usd(
            "unknown-model",
            input_tokens=1000,
            output_tokens=1000,
            pricing_table=DEFAULT_MODEL_PRICING,
        )
    assert cost == Decimal("0")
    assert "Missing LLM pricing for model" in caplog.text


def test_settings_resolve_llm_provider() -> None:
    settings = Settings()

    assert settings.resolve_llm_provider("gpt-4o-mini") == "openai"
    assert settings.resolve_llm_provider("claude-3-5-haiku-20241022") == "anthropic"
    assert settings.resolve_llm_provider("text-embedding-3-small") == "openai"

    with pytest.raises(ValueError, match="Cannot resolve LLM provider"):
        settings.resolve_llm_provider("llama-3")


def test_settings_total_cost_for_tokens() -> None:
    settings = Settings()
    cost = settings.total_cost_for_tokens("gpt-4o-mini", 1000, 2000)
    expected = Decimal("0.00015") + Decimal("0.0012")
    assert cost == expected


@pytest.mark.asyncio
async def test_anthropic_rejects_multiple_system_messages() -> None:
    settings = Settings(anthropic_api_key="test-key")
    provider = AnthropicProvider(settings)

    with pytest.raises(ValueError, match="at most one system message"):
        await provider.complete(
            [
                LLMMessage(role="system", content="First"),
                LLMMessage(role="system", content="Second"),
                LLMMessage(role="user", content="Hi"),
            ],
            model="claude-3-5-haiku-20241022",
        )


@pytest.mark.asyncio
async def test_anthropic_uses_settings_max_output_tokens() -> None:
    settings = Settings(anthropic_api_key="test-key", llm_max_output_tokens=2048)
    provider = AnthropicProvider(settings)
    mock_response = MagicMock()
    mock_response.content = [MagicMock(type="text", text="ok")]
    mock_response.usage.input_tokens = 1
    mock_response.usage.output_tokens = 1
    mock_response.model = "claude-3-5-haiku-20241022"

    with patch.object(
        provider._client.messages,
        "create",
        new=AsyncMock(return_value=mock_response),
    ) as create:
        await provider.complete(
            [LLMMessage(role="user", content="Hi")],
            model="claude-3-5-haiku-20241022",
        )

    assert create.await_args.kwargs["max_tokens"] == 2048


@pytest.mark.asyncio
async def test_openai_raises_when_choices_empty() -> None:
    settings = Settings(openai_api_key="test-key")
    provider = OpenAIProvider(settings)
    mock_response = MagicMock(choices=[], usage=None, model="gpt-4o-mini")

    with patch.object(
        provider._client.chat.completions,
        "create",
        new=AsyncMock(return_value=mock_response),
    ):
        with pytest.raises(ValueError, match="no choices"):
            await provider.complete(
                [LLMMessage(role="user", content="Hi")],
                model="gpt-4o-mini",
            )


@pytest.mark.asyncio
async def test_openai_warns_when_usage_missing(caplog: pytest.LogCaptureFixture) -> None:
    settings = Settings(openai_api_key="test-key")
    provider = OpenAIProvider(settings)
    mock_choice = MagicMock(message=MagicMock(content="Hi"))
    mock_response = MagicMock(choices=[mock_choice], usage=None, model="gpt-4o-mini")

    with patch.object(
        provider._client.chat.completions,
        "create",
        new=AsyncMock(return_value=mock_response),
    ):
        with caplog.at_level("WARNING"):
            result = await provider.complete(
                [LLMMessage(role="user", content="Hi")],
                model="gpt-4o-mini",
            )

    assert result.input_tokens == 0
    assert result.output_tokens == 0
    assert "omitted usage data" in caplog.text
