"""Onion search provider using Ahmia and specialized dark web discovery."""

import logging
from bs4 import BeautifulSoup
import httpx
from dwi_crawler.discovery.models import SearchResultItem
from dwi_crawler.discovery.providers.base import SearchProvider
from dwi_crawler.discovery.providers.mock import MockSearchProvider
from dwi_crawler.security.validation import URLNormalizer, is_onion_url

logger = logging.getLogger("dwi_crawler.discovery.onion")


class OnionSearchProvider(SearchProvider):
    name: str = "AhmiaOnionSearch"

    def __init__(self, proxy_url: str | None = None, timeout: float = 15.0):
        self.proxy_url = proxy_url
        self.timeout = timeout
        self.fallback = MockSearchProvider(source_type="onion")

    async def search(
        self,
        query: str,
        *,
        max_results: int = 7,
        keyword: str = "",
        company: str = "",
    ) -> list[SearchResultItem]:
        results: list[SearchResultItem] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0",
        }

        # Try surface gateway for Ahmia (or proxy if configured)
        search_url = f"https://ahmia.fi/search/?q={httpx.URL('', params={'q': query}).params['q']}"
        proxy = self.proxy_url if self.proxy_url else None

        try:
            async with httpx.AsyncClient(
                proxy=proxy, timeout=self.timeout, follow_redirects=True
            ) as client:
                resp = await client.get(search_url, headers=headers)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    items = soup.select("li.result")
                    for item in items[:max_results]:
                        link = item.select_one("h4 > a")
                        snippet = item.select_one("p")
                        if link:
                            raw_href = link.get("href", "")
                            # Ahmia links redirect through /search/redirect?url=http://...onion
                            if "redirect?url=" in raw_href:
                                raw_href = raw_href.split("redirect?url=")[-1]

                            canonical = URLNormalizer.normalize(raw_href)
                            if canonical and is_onion_url(canonical):
                                title = link.get_text(strip=True)
                                desc = snippet.get_text(strip=True) if snippet else ""
                                results.append(
                                    SearchResultItem(
                                        url=canonical,
                                        title=title,
                                        description=desc,
                                        search_provider=self.name,
                                        query=query,
                                        keyword=keyword,
                                        company=company,
                                        source_type="onion",
                                        confidence=0.88,
                                    )
                                )
        except Exception as ex:
            logger.warning(f"Onion search request failed: {ex}. Using fallback provider.")

        if not results:
            results = await self.fallback.search(
                query, max_results=max_results, keyword=keyword, company=company
            )

        return results[:max_results]
