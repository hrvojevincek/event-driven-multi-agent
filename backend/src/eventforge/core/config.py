from decimal import Decimal
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from eventforge.core.llm_pricing import DEFAULT_MODEL_PRICING, ModelPricing, compute_cost_usd

LLMProviderName = Literal["openai", "anthropic"]


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env."""
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "local"
    log_level: str = "INFO"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "eventforge"
    postgres_user: str = "eventforge"
    postgres_password: str = "changeme"

    cors_origins: list[str] = Field(default=["http://localhost:3000"])

    aws_region: str = "us-east-1"
    aws_endpoint_url: str | None = "http://localhost:4566"
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"
    event_bus_name: str = "eventforge-bus"
    sqs_queue_prefix: str = "eventforge"
    sqs_wait_time_seconds: int = 20
    sqs_max_messages: int = 10
    sqs_max_receive_count: int = 3

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    tavily_api_key: str = ""
    llm_default_model: str = "gpt-4o-mini"
    llm_max_output_tokens: int = 4096
    embedding_model: str = "text-embedding-3-small"
    embedding_chunk_size_tokens: int = 512
    embedding_chunk_overlap_tokens: int = 50
    knowledge_rag_top_k: int = 10
    knowledge_max_entities: int = 15
    llm_model_pricing: dict[str, ModelPricing] = Field(
        default_factory=lambda: DEFAULT_MODEL_PRICING.copy()
    )

    @property
    def ingestion_queue_name(self) -> str:
        return f"{self.sqs_queue_prefix}-ingestion"

    @property
    def embedding_queue_name(self) -> str:
        return f"{self.sqs_queue_prefix}-embedding"

    @property
    def knowledge_mining_queue_name(self) -> str:
        return f"{self.sqs_queue_prefix}-knowledge-mining"

    @property
    def research_queue_name(self) -> str:
        return f"{self.sqs_queue_prefix}-research"

    @property
    def synthesis_queue_name(self) -> str:
        return f"{self.sqs_queue_prefix}-synthesis"

    @property
    def dlq_queue_name(self) -> str:
        return f"{self.sqs_queue_prefix}-dlq"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def resolve_llm_provider(self, model: str) -> LLMProviderName:
        normalized = model.lower()
        if normalized.startswith("claude"):
            return "anthropic"
        if normalized.startswith(("gpt-", "o1", "o3", "text-embedding")):
            return "openai"
        msg = f"Cannot resolve LLM provider for model: {model}"
        raise ValueError(msg)

    def total_cost_for_tokens(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> Decimal:
        return compute_cost_usd(
            model,
            input_tokens,
            output_tokens,
            self.llm_model_pricing,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
