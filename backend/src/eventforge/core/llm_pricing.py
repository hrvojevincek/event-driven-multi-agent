import logging
from decimal import Decimal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ModelPricing(BaseModel):
    """Per-million-token pricing for one model."""

    input_per_million: Decimal = Field(ge=0)
    output_per_million: Decimal = Field(ge=0)


DEFAULT_MODEL_PRICING: dict[str, ModelPricing] = {
    "gpt-4o-mini": ModelPricing(
        input_per_million=Decimal("0.15"),
        output_per_million=Decimal("0.60"),
    ),
    "gpt-4o": ModelPricing(
        input_per_million=Decimal("2.50"),
        output_per_million=Decimal("10.00"),
    ),
    "claude-3-5-haiku-20241022": ModelPricing(
        input_per_million=Decimal("0.80"),
        output_per_million=Decimal("4.00"),
    ),
    "claude-3-5-sonnet-20241022": ModelPricing(
        input_per_million=Decimal("3.00"),
        output_per_million=Decimal("15.00"),
    ),
    "text-embedding-3-small": ModelPricing(
        input_per_million=Decimal("0.02"),
        output_per_million=Decimal("0.00"),
    ),
}


def resolve_model_pricing(
    model: str,
    pricing_table: dict[str, ModelPricing],
) -> ModelPricing | None:
    """Match a provider model id to configured pricing (exact or versioned prefix)."""
    if model in pricing_table:
        return pricing_table[model]

    # OpenAI returns dated ids like gpt-4o-mini-2024-07-18 — longest prefix wins.
    candidates = sorted(pricing_table.keys(), key=len, reverse=True)
    for key in candidates:
        if model.startswith(f"{key}-"):
            return pricing_table[key]

    return None


def compute_cost_usd(
    model: str,
    input_tokens: int,
    output_tokens: int,
    pricing_table: dict[str, ModelPricing],
) -> Decimal:
    """Calculate USD cost from a model pricing table."""
    pricing = resolve_model_pricing(model, pricing_table)
    if pricing is None:
        logger.warning(
            "Missing LLM pricing for model; cost will be recorded as zero",
            extra={"model": model},
        )
        return Decimal("0")

    million = Decimal("1000000")
    input_cost = (Decimal(input_tokens) / million) * pricing.input_per_million
    output_cost = (Decimal(output_tokens) / million) * pricing.output_per_million
    return input_cost + output_cost
