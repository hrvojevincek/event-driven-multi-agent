import logging

from eventforge.core.config import Settings
from eventforge.services.mock.fixtures import mock_search_results
from eventforge.services.search.types import WebSearchResult

logger = logging.getLogger(__name__)


class MockTavilyClient:
    """Fixture web search — no Tavily API calls."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def search(
        self,
        query: str,
        *,
        max_results: int,
        search_depth: str = "basic",
    ) -> list[WebSearchResult]:
        results = mock_search_results(query, max_results=max_results)
        logger.info(
            "Mock Tavily search completed",
            extra={
                "query_length": len(query),
                "max_results": max_results,
                "search_depth": search_depth,
                "result_count": len(results),
            },
        )
        return results
