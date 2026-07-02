import logging
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from eventforge.core.config import Settings
from eventforge.db.repositories.llm_usage import LLMUsageRepository
from eventforge.services.mock.fixtures import MOCK_MODEL, deterministic_embedding

logger = logging.getLogger(__name__)


class MockEmbeddingClient:
    """Fixture embeddings — no OpenAI API calls."""

    def __init__(
        self,
        settings: Settings,
        session: AsyncSession | None = None,
    ) -> None:
        self._settings = settings
        self._session = session

    async def embed_texts(
        self,
        texts: list[str],
        *,
        job_id: uuid.UUID,
        agent_name: str,
    ) -> list[list[float]]:
        if not texts:
            return []

        embeddings = [deterministic_embedding(text) for text in texts]

        if self._session is not None:
            try:
                await LLMUsageRepository(self._session).log(
                    job_id=job_id,
                    agent_name=agent_name,
                    model=MOCK_MODEL,
                    input_tokens=sum(len(text) for text in texts),
                    output_tokens=0,
                    cost_usd=Decimal("0"),
                )
            except Exception:
                logger.exception(
                    "Failed to log mock embedding usage",
                    extra={
                        "job_id": str(job_id),
                        "agent_name": agent_name,
                    },
                )

        logger.info(
            "Mock embeddings created",
            extra={
                "job_id": str(job_id),
                "agent_name": agent_name,
                "text_count": len(texts),
            },
        )
        return embeddings
