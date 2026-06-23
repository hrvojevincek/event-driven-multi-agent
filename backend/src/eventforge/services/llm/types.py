from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

LLMRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class LLMMessage:
    """One message in a chat completion request."""

    role: LLMRole
    content: str


@dataclass(frozen=True)
class LLMCompletionResult:
    """Normalized result from any LLM provider."""

    content: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
