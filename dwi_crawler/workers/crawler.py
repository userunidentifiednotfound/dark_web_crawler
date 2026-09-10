"""Page Fetch Worker: Dequeues URLs, fetches over Tor/proxy, persists source to CAS, extracts links, and queues new URLs."""

import asyncio
import logging
import time
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from dwi_crawler.config.settings import get_settings
from dwi_crawler.crawling.http_client import HTTPCrawlerClient
from dwi_crawler.crawling.scope import ScopePolicy
from dwi_crawler.database.repositories.company_repository import CompanyRepository
from dwi_crawler.database.repositories.page_repository import PageRepository
from dwi_crawler.database.repositories.url_repository import URLRepository
from dwi_crawler.database.session import get_async_session_factory
from dwi_crawler.processing.links import LinkExtractor
from dwi_crawler.queue.manager import QueueManager
from dwi_crawler.security.validation import URLNormalizer

logger = logging.getLogger("dwi_crawler.workers.crawler")


class PageFetchWorker:
    """Worker 2: High-throughput async HTTP crawler with CAS storage and link discovery."""

    def __init__(self, worker_id: str | None = None):
        self.worker_id = worker_id or f"crawler-{uuid.uuid4().hex[:8]}"
        self.http_client = HTTPCrawlerClient()
        self.settings = get_settings()
        self.session_factory = get_async_session_factory()
        self.scope_policy = ScopePolicy()
        self.is_running = False

    async def process_one_job(self) -> bool:
        """Pulls and executes a single job from the crawl queue. Returns True if a job was processed."""
        async with self.session_factory() as session:
            queue_mgr = QueueManager(session)
            # Periodic stale job recovery
            await queue_mgr.recover_stale_jobs(timeout_seconds=90)

            job = await queue_mgr.acquire_next_job(self.worker_id)
            if not job:
                return False

            page_repo = PageRepository(session)
            url_repo = URLRepository(session)

            logger.info(f"[{self.worker_id}] Processing job {job.job_id} -> {job.url} (depth={job.depth})")
            start_time = time.time()

            # Scope policy verification
            if not self.scope_policy.is_allowed_to_crawl(job.url):
                logger.info(f"URL {job.url} skipped: excluded by active scope policy ({self.scope_policy.mode}).")
                await url_repo.update_status(job.discovered_url_id, "SKIPPED")
                await queue_mgr.mark_success(job.id)
                await session.commit()
                return True

            # Mark URL as crawling
            await url_repo.update_status(job.discovered_url_id, "CRAWLING")
            await session.commit()

        # Fetch over HTTP client
        fetch_res = await self.http_client.fetch(job.url)
        duration = round(time.time() - start_time, 2)

        async with self.session_factory() as session:
            queue_mgr = QueueManager(session)
            page_repo = PageRepository(session)
            url_repo = URLRepository(session)

            if fetch_res.is_captcha:
                logger.warning(f"CAPTCHA / gatekeeper detected on {job.url}: {fetch_res.captcha_type}. Attempting headless auto-click resolution...")
                # Attempt automated resolution via BrowserManager before marking manual intervention
                try:
                    from dwi_crawler.crawling.browser import get_browser_manager
                    browser_res = await get_browser_manager().render_page(job.url, is_onion=True)
                    if browser_res.success and browser_res.html and len(browser_res.html) > 200:
                        logger.info(f"Auto-click / browser challenge bypass succeeded for {job.url}")
                        fetch_res = fetch_res._replace(
                            content_bytes=browser_res.html.encode("utf-8"),
                            status_code=200,
                            is_captcha=False,
                            final_url=browser_res.current_url or job.url,
                            error=None,
                        )
                except Exception as b_err:
                    logger.debug(f"Headless browser auto-click attempt failed for {job.url}: {b_err}")

            if fetch_res.is_captcha:
                logger.warning(f"CAPTCHA challenge remains on {job.url}: {fetch_res.captcha_type}")
                await queue_mgr.mark_captcha_required(
                    job.id, job.url, job.company_id, fetch_res.captcha_type
                )
                await url_repo.update_status(job.discovered_url_id, "CAPTCHA_REQUIRED")
                await session.commit()
                return True

            if fetch_res.status_code == 0 or fetch_res.error:
                err_msg = fetch_res.error or f"HTTP status {fetch_res.status_code}"
                logger.error(f"[{self.worker_id}] Fetch failed for {job.url}: {err_msg}")
                await queue_mgr.mark_failed(job.id, err_msg)
                await url_repo.update_status(job.discovered_url_id, "FAILED")
                await session.commit()
                return True

            # Save full page source to Content-Addressable Storage & PageVersion
            canonical_url = URLNormalizer.normalize(job.url)
            url_hash = URLNormalizer.fingerprint(canonical_url)

            page, version, is_new_content = await page_repo.save_page_fetch(
                discovered_url_id=job.discovered_url_id,
                company_id=job.company_id,
                canonical_url=canonical_url,
                url_hash=url_hash,
                raw_bytes=fetch_res.content_bytes,
                mime_type=fetch_res.mime_type,
                http_status=fetch_res.status_code,
                headers_dict=fetch_res.headers,
                final_url=fetch_res.final_url,
                redirect_chain=fetch_res.redirect_chain,
            )

            # Link Extraction & New URL Discovery (Section 25, 26, 27)
            if "html" in fetch_res.mime_type or "text" in fetch_res.mime_type:
                extracted_links = LinkExtractor.extract_links(
                    fetch_res.content_bytes, base_url=fetch_res.final_url or job.url
                )
                await page_repo.save_extracted_links(page.id, extracted_links)

                # Recursive Bounded Discovery
                next_depth = job.depth + 1
                if next_depth <= self.settings.max_depth:
                    for el in extracted_links:
                        try:
                            disc_rec, is_new = await url_repo.save_or_increment(
                                raw_url=el.raw_url,
                                company_id=job.company_id,
                                source_type="onion" if el.is_onion else "surface",
                                discovered_from=canonical_url,
                                priority=job.priority,
                                depth=next_depth,
                            )
                            # Queue newly discovered link if permitted by scope
                            if is_new and self.scope_policy.is_allowed_to_crawl(disc_rec.canonical_url):
                                await queue_mgr.enqueue_url(
                                    discovered_url_id=disc_rec.id,
                                    company_id=job.company_id,
                                    url=disc_rec.canonical_url,
                                    parent_url=canonical_url,
                                    depth=next_depth,
                                    priority=disc_rec.priority,
                                )
                        except Exception as e:
                            logger.debug(f"Link discovery insertion skipped for {el.raw_url}: {e}")

            # Mark job successful and URL crawled
            await queue_mgr.mark_success(job.id)
            await url_repo.update_status(job.discovered_url_id, "CRAWLED")
            await session.commit()

            logger.info(
                f"[{self.worker_id}] Crawled successfully: {job.url} "
                f"(status={fetch_res.status_code}, bytes={len(fetch_res.content_bytes)}, "
                f"duration={duration}s, new_content={is_new_content})"
            )
            return True

    async def start_loop(self, max_idle_sleep: float = 2.0) -> None:
        """Continuous crawler worker execution loop."""
        self.is_running = True
        logger.info(f"[{self.worker_id}] Page fetch crawler worker started.")
        while self.is_running:
            try:
                processed = await self.process_one_job()
                if not processed:
                    await asyncio.sleep(max_idle_sleep)
            except Exception as ex:
                logger.error(f"[{self.worker_id}] Worker error: {ex}", exc_info=True)
                await asyncio.sleep(max_idle_sleep)
