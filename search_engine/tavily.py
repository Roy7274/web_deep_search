from abc import ABC
from typing import Literal, Optional, List

from tavily import TavilyClient

from .search_engine import SearchEngine, SearchResult, SearchReference

import asyncio


class TavilySearchEngine(SearchEngine, ABC):

    def __init__(
            self,
            api_key: str,
            search_depth: Literal["basic", "advanced"] = "basic",
            topic: Literal["general", "news"] = "general",
            days: int = 3,
            max_results: int = 5,
            include_domains: Optional[str] = None,
            exclude_domains: Optional[str] = None,
    ):
        super().__init__()
        self._tavily_client = TavilyClient(api_key=api_key)
        self._search_depth = search_depth
        self._topic = topic
        self._days = days
        self._max_results = max_results
        self._include_domains = include_domains
        self._exclude_domains = exclude_domains

    def search(self, queries: List[str]) -> List[SearchResult]:
        return asyncio.run(self.asearch(queries=queries))

    async def asearch(self, queries: List[str]) -> List[SearchResult]:
        tasks = [self._arun_search_single(query) for query in queries]
        task_results = await asyncio.gather(*tasks)
        return [
            r for r in task_results
        ]

    async def _arun_search_single(self, query: str) -> SearchResult:
        return await asyncio.to_thread(self._search_single, query)

    def _search_single(self, query: str) -> SearchResult:
        response = self._tavily_client.search(
            query=query,
            search_depth=self._search_depth,
            topic=self._topic,
            days=self._days,
            max_results=self._max_results,
            include_domains=self._include_domains,
            exclude_domains=self._exclude_domains,
        )
        results = response.get("results", [])
        search_references = [
            SearchReference(
                title=r.get("title"),
                url=r.get("url"),
                content=r.get("content"),
                site=None,
            )
            for r in results
        ]
        return SearchResult(
            query=query,
            summary_content=self._format_result(response),
            search_references=search_references,
        )

    @classmethod
    def _format_result(cls, tavily_result: dict) -> str:
        results = tavily_result.get("results", [])
        formatted: str = ""
        for (i, result) in enumerate(results):
            formatted += f"参考资料{i + 1}: \n"
            formatted += f"标题: {result.get('title', '')}\n"
            formatted += f"内容: {result.get('content', '')}\n"
            formatted += "\n"
        return formatted
