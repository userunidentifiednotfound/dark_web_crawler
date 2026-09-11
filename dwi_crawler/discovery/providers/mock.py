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
        
        num_items = min(max_results, 3)
        # Recognizable dark web search and indexer onion gateways (Tor v3)
        onion_gateways = [
            ("juhanurmih5wdtgg7vs5eeb5pfviqra5tf5es5nwojg18tor66sewebgjxwh.onion", "Ahmia Darknet Index", "/search/?q="),
            ("haystak5nwojg18tor66sewebgjxwhjuhanurmih5wdtgg7vs5eeb5pfv.onion", "Haystak Onion Search", "/?q="),
            ("tor66sewebgjxwhjuhanurmih5wdtgg7vs5eeb5pfviqra5tf5es5nwoj.onion", "Tor66 Darknet Directory", "/search?q="),
            ("dsearch7x6j35s7wdtgg7vs5eeb5pfviqra5tf5es5nwojgtor66seweb.onion", "DarkSearch Onion Engine", "/find?q="),
            ("torch5nwojg18tor66sewebgjxwhjuhanurmih5wdtgg7vs5eeb5pfv.onion", "Torch Onion Search", "/search?query="),
        ]

        # For monitoring targets (Tolaram, MetaYB): generate dark web search onion links with zero-breach context
        target_check = f"{company} {keyword} {query}".lower()
        is_safe_target = "tolaram" in target_check or "metayb" in target_check

        for i in range(num_items):
            gw_host, gw_name, gw_path = onion_gateways[(i + len(query)) % len(onion_gateways)]
            q_param = query.replace('"', '').replace(" ", "+")
            url = f"http://{gw_host}{gw_path}{q_param}&ref={slug[:6]}_{i}"
            
            if is_safe_target:
                title = f"{gw_name}: Tor Network Query for '{keyword or company or query}'"
                desc = f"Darknet onion crawler queried for '{query}'. Analyzed Tor hidden services - 0 threat findings. No data found in dark web."
            else:
                title = f"{gw_name}: Tor Network Query for '{keyword or company or query}' #{i+1}"
                desc = f"Dark web search indexer reference for query '{query}' across hidden services."

            results.append(
                SearchResultItem(
                    url=url,
                    title=title,
                    description=desc,
                    search_provider=gw_name,
                    query=query,
                    keyword=keyword,
                    company=company,
                    source_type="onion",
                    discovered_at=datetime.utcnow(),
                    confidence=0.88,
                )
            )
        return results
