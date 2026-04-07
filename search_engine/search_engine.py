from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Optional, List

"""
single reference definition
"""


class SearchReference(BaseModel):
    site: Optional[str]
    title: Optional[str]
    url: Optional[str]
    content: Optional[str]


"""
search_result definition
"""


class SearchResult(BaseModel):
    # query is the input question
    query: str = ""
    # summary_content is a summary plain text of the query result.
    summary_content: Optional[str] = None
    # search_references is the raw references of searched result
    search_references: Optional[List[SearchReference]] = None


"""
search_engine interface
"""


class SearchEngine(BaseModel, ABC):

    @abstractmethod
    def search(self, queries: List[str]) -> List[SearchResult]:
        pass

    @abstractmethod
    async def asearch(self, queries: List[str]) -> List[SearchResult]:
        pass
