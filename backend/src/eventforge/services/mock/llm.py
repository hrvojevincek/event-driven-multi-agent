import logging
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from eventforge.core.config import Settings
from eventforge.core.otel import agent_span, set_event_attributes
from eventforge.db.repositories.llm_usage import LLMUsageRepository
from eventforge.events.schemas.constants import (
    WORKER_NAME_KNOWLEDGE,
    WORKER_NAME_RESEARCH,
    WORKER_NAME_SYNTHESIS,
)
from eventforge.services.llm.types import LLMCompletionResult, LLMMessage
from eventforge.services.mock.fixtures import (
    MOCK_MODEL,
    mock_entity_extraction_json,
    mock_research_note_markdown,
    mock_sub_queries_json,
    mock_synthesis_report_markdown,
)

logger = logging.getLogger(__name__)


class MockLLMClient:
    """Fixture chat completions — no OpenAI/Anthropic API calls."""

    def __init__(
        self,
        settings: Settings,
        session: AsyncSession | None = None,
    ) -> None:
        self._settings = settings
        self._session = session

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        job_id: uuid.UUID,
        agent_name: str,
        model: str | None = None,
        max_tokens: int | None = None,
    ) -> LLMCompletionResult:
        resolved_model = model or self._settings.llm_default_model
        user_content = next((message.content for message in reversed(
            messages) if message.role == "user"), "", )
        system_content = next(
            (message.content for message in messages
             if message.role == "system"),
            "",)

        with agent_span(
            agent_name,
            "complete",
            job_id=str(job_id),
        ) as span:
            set_event_attributes(span, model=MOCK_MODEL, agent_name=agent_name)

            content = self._mock_content(
                agent_name, system_content, user_content)
            result = LLMCompletionResult(
                content=content,
                model=MOCK_MODEL,
                input_tokens=100,
                output_tokens=max(len(content) // 4, 1),
                cost_usd=Decimal("0"),
            )

            set_event_attributes(
                span,
                model=result.model,
                token_count=result.input_tokens + result.output_tokens,
            )

            if self._session is not None:
                try:
                    await LLMUsageRepository(self._session).log(
                        job_id=job_id,
                        agent_name=agent_name,
                        model=result.model,
                        input_tokens=result.input_tokens,
                        output_tokens=result.output_tokens,
                        cost_usd=result.cost_usd,
                    )
                except Exception:
                    logger.exception(
                        "Failed to log mock LLM usage",
                        extra={
                            "job_id": str(job_id),
                            "agent_name": agent_name,
                        },
                    )

            logger.info(
                "Mock LLM completion",
                extra={
                    "job_id": str(job_id),
                    "agent_name": agent_name,
                    "resolved_model": resolved_model,
                    "max_tokens": max_tokens,
                },
            )
            return result

    def _mock_content(
        self,
        agent_name: str,
        system_content: str,
        user_content: str,
    ) -> str:
        if agent_name == WORKER_NAME_KNOWLEDGE:
            return mock_entity_extraction_json(user_content)
        if agent_name == WORKER_NAME_SYNTHESIS:
            return mock_synthesis_report_markdown(user_content)
        if agent_name == WORKER_NAME_RESEARCH:
            if "JSON array of strings" in system_content:
                return mock_sub_queries_json(user_content)
            return mock_research_note_markdown(user_content)
        return f"Mock completion for agent `{agent_name}`."
