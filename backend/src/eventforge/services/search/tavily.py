import logging

import httpx

from eventforge.core.config import Settings, get_settings
from eventforge.events.schemas import QueryDepth
from eventforge.services.resilience.errors import is_retryable_httpx_error
from eventforge.services.resilience.external_call import call_with_resilience
from eventforge.services.search.types import WebSearchResult

logger = logging.getLogger(__name__)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
MAX_SNIPPET_LENGTH = 8000
MAX_TITLE_LENGTH = 512
MAX_URL_LENGTH = 2048

DEFAULT_SOURCE_COUNT_BY_DEPTH: dict[QueryDepth, int] = {
    QueryDepth.QUICK: 3,
    QueryDepth.STANDARD: 5,
    QueryDepth.DEEP: 10,
}

TAVILY_SEARCH_DEPTH_BY_QUERY_DEPTH: dict[QueryDepth, str] = {
    QueryDepth.QUICK: "basic",
    QueryDepth.STANDARD: "basic",
    QueryDepth.DEEP: "advanced",
}


def resolve_source_count(*, depth: str, max_sources: int | None) -> int:
    """Return how many sources to fetch, honoring explicit max_sources over depth defaults."""
    if max_sources is not None:
        return max_sources
    return DEFAULT_SOURCE_COUNT_BY_DEPTH[QueryDepth(depth)]


def resolve_tavily_search_depth(depth: str) -> str:
    """Map job depth preset to Tavily search_depth (basic vs advanced)."""
    return TAVILY_SEARCH_DEPTH_BY_QUERY_DEPTH[QueryDepth(depth)]


class TavilyClient:
    """Research web search via the Tavily API."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def search(
        self,
        query: str,
        *,
        max_results: int,
        search_depth: str = "basic",
    ) -> list[WebSearchResult]:
        if not self._settings.tavily_api_key:
            msg = "TAVILY_API_KEY is not configured"
            raise ValueError(msg)

        payload = {
            "query": query,
            "max_results": max(1, min(max_results, 20)),
            "search_depth": search_depth,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._settings.tavily_api_key}",
        }

        async def _search() -> list[WebSearchResult]:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(TAVILY_SEARCH_URL, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

            results: list[WebSearchResult] = []
            for item in data.get("results", []):
                url = (item.get("url") or "").strip()
                if not url:
                    continue
                title = (item.get("title") or url or "Untitled").strip()
                content = (item.get("content") or "").strip()
                results.append(
                    WebSearchResult(
                        url=url[:MAX_URL_LENGTH],
                        title=title[:MAX_TITLE_LENGTH],
                        snippet=(content or title)[:MAX_SNIPPET_LENGTH],
                    )
                )
            return results

        results = await call_with_resilience(
            "tavily",
            _search,
            settings=self._settings,
            is_retryable=is_retryable_httpx_error,
        )

        logger.info(
            "Tavily search completed",
            extra={
                "query_length": len(query),
                "max_results": max_results,
                "search_depth": search_depth,
                "result_count": len(results),
            },
        )
        return results


def get_tavily_client(settings: Settings | None = None) -> TavilyClient:
    """Build a Tavily search client from application settings."""
    resolved = settings or get_settings()
    if resolved.use_mock_external_apis:
        from eventforge.services.mock.tavily import MockTavilyClient

        return MockTavilyClient(resolved)  # type: ignore[return-value]
    return TavilyClient(resolved)
