from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
