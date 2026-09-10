"""Browser Worker: Dedicated headless Selenium worker for JavaScript-rendered targets and CAPTCHA."""

import asyncio
import logging
import uuid
from dwi_crawler.crawling.browser import get_browser_manager
from dwi_crawler.database.repositories.page_repository import PageRepository
from dwi_crawler.database.repositories.url_repository import URLRepository
from dwi_crawler.database.session import get_async_session_factory
from dwi_crawler.processing.links import LinkExtractor
from dwi_crawler.queue.manager import QueueManager
from dwi_crawler.security.validation import URLNormalizer, is_onion_url

logger = logging.getLogger("dwi_crawler.workers.browser")


class BrowserWorker:
    """Worker 3: Controlled Selenium pool for rendering dynamic JS pages and solving challenges."""

    def __init__(self, worker_id: str | None = None):
        self.worker_id = worker_id or f"browser-{uuid.uuid4().hex[:8]}"
        self.browser_manager = get_browser_manager()
        self.session_factory = get_async_session_factory()
        self.is_running = False

    async def render_url(self, url: str, company_id: int, discovered_url_id: int) -> bool:
        """Executes browser rendering and stores source."""
        is_onion = is_onion_url(url)
        logger.info(f"[{self.worker_id}] Executing browser render for {url}")

        render_res = await self.browser_manager.render_page(
            url, capture_screenshot=True, is_onion=is_onion
        )

        if not render_res.success or not render_res.html:
            logger.error(f"[{self.worker_id}] Browser render failed for {url}: {render_res.error}")
            return False

        canonical = URLNormalizer.normalize(url)
        url_hash = URLNormalizer.fingerprint(canonical)
        raw_bytes = render_res.html.encode("utf-8")

        async with self.session_factory() as session:
            page_repo = PageRepository(session)
            url_repo = URLRepository(session)

            page, version, is_new = await page_repo.save_page_fetch(
                discovered_url_id=discovered_url_id,
                company_id=company_id,
                canonical_url=canonical,
                url_hash=url_hash,
                raw_bytes=raw_bytes,
                mime_type="text/html",
                http_status=200,
                headers_dict={"Content-Type": "text/html; charset=utf-8"},
                final_url=render_res.current_url,
                redirect_chain=[],
                screenshot_bytes=render_res.screenshot_bytes,
            )

            # Link extraction
            links = LinkExtractor.extract_links(render_res.html, base_url=render_res.current_url or url)
            await page_repo.save_extracted_links(page.id, links)
            await url_repo.update_status(discovered_url_id, "CRAWLED")
            await session.commit()

        logger.info(f"[{self.worker_id}] Browser page saved: {len(raw_bytes)} bytes, {len(links)} links.")
        return True

    async def start_loop(self, poll_interval: float = 5.0) -> None:
        self.is_running = True
        logger.info(f"[{self.worker_id}] Browser worker loop started.")
        while self.is_running:
            await asyncio.sleep(poll_interval)
