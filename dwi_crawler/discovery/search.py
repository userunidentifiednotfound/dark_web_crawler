"""Configurable search strategy executing bounded 3 surface and 7 onion discovery queries."""

import asyncio
import logging
from dwi_crawler.config.settings import get_settings
from dwi_crawler.discovery.enhancer import KeywordEnhancer
from dwi_crawler.discovery.models import SearchResultItem
from dwi_crawler.discovery.providers.base import SearchProvider
from dwi_crawler.discovery.providers.onion import OnionSearchProvider
from dwi_crawler.discovery.providers.surface import SurfaceSearchProvider

logger = logging.getLogger("dwi_crawler.discovery.search")


class SearchStrategy:
    """Coordinates search query generation and bounded execution."""

    def __init__(
        self,
        surface_provider: SearchProvider | None = None,
        onion_provider: SearchProvider | None = None,
    ):
        settings = get_settings()
        self.surface_provider = surface_provider or SurfaceSearchProvider(timeout=settings.request_timeout)
        self.onion_provider = onion_provider or OnionSearchProvider(
            proxy_url=settings.get_proxy_url() if settings.use_proxy_for_onion else None,
            timeout=settings.request_timeout,
        )
        self.settings = settings

    async def execute_discovery(
        self,
        keyword: str,
        *,
        company_name: str = "",
        domain: str = "",
    ) -> list[SearchResultItem]:
        """Executes strictly up to 10 searches: 3 surface and 7 onion queries per keyword."""
        query_set = KeywordEnhancer.enhance_keyword(
            keyword=keyword,
            company_name=company_name,
            domain=domain,
        )

        all_results: list[SearchResultItem] = []
        sem = asyncio.Semaphore(self.settings.search_concurrency)

        async def run_surface_query(q: str):
            async with sem:
                try:
                    res = await self.surface_provider.search(
                        q,
                        max_results=self.settings.search_surface_limit,
                        keyword=keyword,
                        company=company_name,
                    )
                    return res
                except Exception as e:
                    logger.error(f"Error in surface search '{q}': {e}")
                    return []

        async def run_onion_query(q: str):
            async with sem:
                try:
                    res = await self.onion_provider.search(
                        q,
                        max_results=self.settings.search_onion_limit,
                        keyword=keyword,
                        company=company_name,
                    )
                    return res
                except Exception as e:
                    logger.error(f"Error in onion search '{q}': {e}")
                    return []

        tasks = []
        # 3 Surface Queries
        for sq in query_set.surface_queries[:3]:
            tasks.append(run_surface_query(sq))

        # 7 Onion Queries
        for oq in query_set.onion_queries[:7]:
            tasks.append(run_onion_query(oq))

        results_lists = await asyncio.gather(*tasks)
        for res_list in results_lists:
            all_results.extend(res_list)

        logger.info(
            f"Discovery complete for '{keyword}': executed {len(tasks)} queries "
            f"(3 surface, 7 onion), found {len(all_results)} candidate results."
        )
        return all_results
