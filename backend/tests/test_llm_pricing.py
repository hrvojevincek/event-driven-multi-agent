from decimal import Decimal

import pytest

from eventforge.core.config import Settings
from eventforge.core.llm_pricing import DEFAULT_MODEL_PRICING, compute_cost_usd


def test_compute_cost_usd_gpt4o_mini() -> None:
    cost = compute_cost_usd(
        "gpt-4o-mini",
        input_tokens=1_000_000,
        output_tokens=500_000,
        pricing_table=DEFAULT_MODEL_PRICING,
    )
    assert cost == Decimal("0.45")


def test_compute_cost_usd_unknown_model_returns_zero() -> None:
    cost = compute_cost_usd(
        "unknown-model",
        input_tokens=1000,
        output_tokens=1000,
        pricing_table=DEFAULT_MODEL_PRICING,
    )
    assert cost == Decimal("0")


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
