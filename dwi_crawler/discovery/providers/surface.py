"""Surface search provider using public search services with graceful fallback."""

import logging
from bs4 import BeautifulSoup
import httpx
from dwi_crawler.discovery.models import SearchResultItem
from dwi_crawler.discovery.providers.base import SearchProvider
from dwi_crawler.discovery.providers.mock import MockSearchProvider
from dwi_crawler.security.validation import URLNormalizer

logger = logging.getLogger("dwi_crawler.discovery.surface")


class SurfaceSearchProvider(SearchProvider):
    name: str = "SurfaceSearch"

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.fallback = MockSearchProvider(source_type="surface")

    async def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        keyword: str = "",
        company: str = "",
    ) -> list[SearchResultItem]:
        results: list[SearchResultItem] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        try:
            # Query DuckDuckGo Lite HTML interface
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.post(
                    "https://lite.duckduckgo.com/lite/",
                    data={"q": query},
                    headers=headers,
                )
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    links = soup.select("a.result-link")
                    snippets = soup.select("td.result-snippet")
                    
                    for i, link in enumerate(links[:max_results]):
                        raw_href = link.get("href", "")
                        title = link.get_text(strip=True)
                        desc = snippets[i].get_text(strip=True) if i < len(snippets) else ""
                        
                        canonical = URLNormalizer.normalize(raw_href)
                        if canonical and canonical.startswith("http"):
                            results.append(
                                SearchResultItem(
                                    url=canonical,
                                    title=title,
                                    description=desc,
                                    search_provider=self.name,
                                    query=query,
                                    keyword=keyword,
                                    company=company,
                                    source_type="surface",
                                    confidence=0.75,
                                )
                            )
        except Exception as ex:
            logger.warning(f"Surface search provider encountered error: {ex}. Using fallback.")

        if not results:
            results = await self.fallback.search(
                query, max_results=max_results, keyword=keyword, company=company
            )

        return results[:max_results]
