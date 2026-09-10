"""Mock search provider for testing, sandbox environments, and dry runs."""

import hashlib
from datetime import datetime
from dwi_crawler.discovery.models import SearchResultItem
from dwi_crawler.discovery.providers.base import SearchProvider


class MockSearchProvider(SearchProvider):
    name: str = "MockSearch"

    def __init__(self, source_type: str = "onion"):
        self.source_type = source_type

    async def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        keyword: str = "",
        company: str = "",
    ) -> list[SearchResultItem]:
        results: list[SearchResultItem] = []
        slug = hashlib.md5(query.encode()).hexdigest()[:10]
        
        # Generate deterministic mock results matching the query context
        num_items = min(max_results, 3)
        for i in range(num_items):
            if self.source_type == "onion":
                onion_hash = hashlib.sha256(f"{query}-{i}".encode()).hexdigest()[:56]
                url = f"http://{onion_hash}.onion/leaks/{slug}_{i}"
                title = f"Dark Market Leak: {keyword or company} Document Dump #{i+1}"
                desc = f"Archive dump containing internal database records, emails, and credentials for {company or keyword} matching '{query}'."
            else:
                url = f"https://pastebin-mirror.org/archive/{slug}_{i}.html"
                title = f"Security Intelligence Advisory - {keyword or company}"
                desc = f"Public intelligence advisory mentioning exposed endpoints for {company or keyword} from query '{query}'."

            results.append(
                SearchResultItem(
                    url=url,
                    title=title,
                    description=desc,
                    search_provider=self.name,
                    query=query,
                    keyword=keyword,
                    company=company,
                    source_type=self.source_type,
                    discovered_at=datetime.utcnow(),
                    confidence=0.85 if "leak" in query or "database" in query else 0.70,
                )
            )
        return results
