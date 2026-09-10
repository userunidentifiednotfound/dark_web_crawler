"""Discovery Worker: Executes bounded search queries, extracts, normalizes, deduplicates, and queues URLs."""

import asyncio
import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from dwi_crawler.database.repositories.company_repository import CompanyRepository
from dwi_crawler.database.repositories.search_repository import SearchRepository
from dwi_crawler.database.repositories.url_repository import URLRepository
from dwi_crawler.database.session import get_async_session_factory
from dwi_crawler.discovery.models import SearchResultItem
from dwi_crawler.discovery.search import SearchStrategy
from dwi_crawler.queue.manager import QueueManager

logger = logging.getLogger("dwi_crawler.workers.discovery")


class DiscoveryWorker:
    """Worker 1: Executes intelligence discovery searches and enqueues candidate URLs."""

    def __init__(self, worker_id: str | None = None):
        self.worker_id = worker_id or f"discovery-{uuid.uuid4().hex[:8]}"
        self.search_strategy = SearchStrategy()
        self.session_factory = get_async_session_factory()
        self.is_running = False

    async def run_for_company(
        self,
        company_id: int,
        *,
        keyword_id: int | None = None,
        search_only: bool = False,
    ) -> list[SearchResultItem]:
        """Runs bounded surface (3) and onion (7) searches for a target company."""
        logger.info(f"[{self.worker_id}] Starting discovery for company {company_id}")
        discovered_items: list[SearchResultItem] = []

        async with self.session_factory() as session:
            comp_repo = CompanyRepository(session)
            url_repo = URLRepository(session)
            search_repo = SearchRepository(session)
            queue_mgr = QueueManager(session)

            company = await comp_repo.get_by_id(company_id)
            if not company:
                logger.error(f"Company ID {company_id} not found.")
                return []

            # Determine primary domain from assets
            primary_domain = ""
            for asset in company.assets:
                if asset.asset_type in ("domain", "brand") and not primary_domain:
                    primary_domain = asset.value

            # Determine keywords to search
            keywords_to_process = []
            if keyword_id:
                for kw in company.keywords:
                    if kw.id == keyword_id and kw.is_active:
                        keywords_to_process.append(kw)
            else:
                keywords_to_process = [kw for kw in company.keywords if kw.is_active]

            # If company has no keywords registered, fallback to company name
            terms = [(kw.id, kw.term) for kw in keywords_to_process]
            if not terms:
                terms = [(None, company.name)]

            for kw_id, term in terms:
                logger.info(f"[{self.worker_id}] Executing 10 searches for keyword: '{term}'")
                results = await self.search_strategy.execute_discovery(
                    keyword=term,
                    company_name=company.name,
                    domain=primary_domain,
                )
                discovered_items.extend(results)

                # Record Search Run
                await search_repo.record_search_run(
                    company_id=company.id,
                    provider="UnifiedDiscoveryStrategy",
                    query=term,
                    source_type="onion",
                    results=results,
                    keyword_id=kw_id,
                )

                # URL Normalization, Deduplication, and Queuing
                for res in results:
                    try:
                        disc_url, is_new = await url_repo.save_or_increment(
                            raw_url=res.url,
                            company_id=company.id,
                            keyword_id=kw_id,
                            source_type=res.source_type,
                            discovered_from=f"search:{res.search_provider}",
                            search_query=res.query,
                            priority=2 if res.source_type == "onion" else 1,
                            depth=0,
                        )

                        if not search_only and is_new:
                            # Only queue newly discovered URLs
                            await queue_mgr.enqueue_url(
                                discovered_url_id=disc_url.id,
                                company_id=company.id,
                                url=disc_url.canonical_url,
                                parent_url=None,
                                depth=0,
                                priority=disc_url.priority,
                            )
                    except Exception as ex:
                        logger.warning(f"Error handling URL {res.url}: {ex}")

            await session.commit()

        logger.info(f"[{self.worker_id}] Discovery finished: found {len(discovered_items)} total candidates.")
        return discovered_items

    async def start_loop(self, poll_interval: float = 30.0) -> None:
        """Continuously monitors active companies for discovery needs."""
        self.is_running = True
        logger.info(f"[{self.worker_id}] Discovery worker daemon started.")
        while self.is_running:
            try:
                async with self.session_factory() as session:
                    comp_repo = CompanyRepository(session)
                    companies = await comp_repo.list_companies()
                    for comp in companies:
                        await self.run_for_company(comp.id)
            except Exception as e:
                logger.error(f"Error in discovery worker loop: {e}")
            await asyncio.sleep(poll_interval)
