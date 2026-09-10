"""Base search provider interface."""

from abc import ABC, abstractmethod
from dwi_crawler.discovery.models import SearchResultItem


class SearchProvider(ABC):
    """Abstract interface for surface and onion search providers."""
    name: str = "base"

    @abstractmethod
    async def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        keyword: str = "",
        company: str = "",
    ) -> list[SearchResultItem]:
        """Executes a search query and returns structured results."""
        pass
