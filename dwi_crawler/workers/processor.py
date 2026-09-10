"""Processing Worker: Parses stored HTML, extracts threat entities, correlates company keywords, and produces findings."""

import asyncio
import logging
import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from dwi_crawler.database.repositories.company_repository import CompanyRepository
from dwi_crawler.database.repositories.finding_repository import FindingRepository
from dwi_crawler.database.session import get_async_session_factory
from dwi_crawler.dwi_client.client import get_dwi_client
from dwi_crawler.models.page import Page
from dwi_crawler.processing.entities import EntityExtractor
from dwi_crawler.processing.keywords import KeywordMatcher
from dwi_crawler.processing.parser import HTMLParser
from dwi_crawler.storage.content import get_content_storage

logger = logging.getLogger("dwi_crawler.workers.processor")


class ProcessingWorker:
    """Worker 4: Asynchronous intelligence processor analyzing raw pages for threat findings and IOCs."""

    def __init__(self, worker_id: str | None = None):
        self.worker_id = worker_id or f"processor-{uuid.uuid4().hex[:8]}"
        self.session_factory = get_async_session_factory()
        self.cas = get_content_storage()
        self.dwi_client = get_dwi_client()
        self.is_running = False

    async def process_page(self, page_id: int) -> dict[str, int]:
        """Analyzes a specific page: extracts text, entities, matches company keywords, and creates findings."""
        stats = {"entities": 0, "findings": 0, "intelligence_records": 0}

        async with self.session_factory() as session:
            comp_repo = CompanyRepository(session)
            finding_repo = FindingRepository(session)

            # Load page with latest version
            stmt = select(Page).where(Page.id == page_id).options(selectinload(Page.versions))
            res = await session.execute(stmt)
            page = res.scalar_one_or_none()
            if not page or not page.versions:
                return stats

            latest_version = page.versions[-1]
            try:
                raw_bytes = self.cas.retrieve_content(latest_version.content_uri)
            except Exception as ex:
                logger.error(f"Failed to read content from CAS {latest_version.content_uri}: {ex}")
                return stats

            # 1. Parse HTML into clean visible text
            parsed = HTMLParser.parse(raw_bytes)
            full_text = f"{parsed.title}\n{' '.join(parsed.headings)}\n{parsed.text}"

            # 2. Extract IOC Entities (Emails, IPs, Crypto, Hashes, Handles)
            entities = EntityExtractor.extract_entities(full_text)
            if entities:
                obs = await finding_repo.save_entities(
                    page_id=page.id,
                    company_id=page.company_id,
                    entities=entities,
                )
                stats["entities"] = len(obs)
                for ent in entities:
                    await self.dwi_client.register_entity({
                        "entity_type": ent.entity_type,
                        "value": ent.value,
                        "page_id": page.id,
                    })

            # 3. Keyword Matching against Company profile
            company = await comp_repo.get_by_id(page.company_id)
            if company:
                kw_pairs = [(k.id, k.term) for k in company.keywords if k.is_active]
                # Also include company name and assets
                kw_pairs.append((None, company.name))
                for a in company.assets:
                    if a.asset_type in ("domain", "brand", "identity"):
                        kw_pairs.append((None, a.value))

                matches = KeywordMatcher.match_content(full_text, kw_pairs)
                for m in matches:
                    # Save intelligence record
                    rec = await finding_repo.save_intelligence_record(
                        company_id=company.id,
                        page_id=page.id,
                        match=m,
                        url=page.canonical_url,
                        source_type="onion" if ".onion" in page.canonical_url else "surface",
                    )
                    stats["intelligence_records"] += 1

                    # If confidence is high or leak/credential context is present, elevate to Finding
                    if m.confidence >= 0.85:
                        title = f"Potential Exposure: {company.name} ({m.term})"
                        desc = f"Keyword match for '{m.term}' detected in Dark Web source ({page.canonical_url})."
                        finding, evidence = await finding_repo.create_finding_with_evidence(
                            company_id=company.id,
                            page_id=page.id,
                            title=title,
                            description=desc,
                            matched_keyword=m.term,
                            source_url=page.canonical_url,
                            content_hash=latest_version.content_hash,
                            context=m.context,
                            severity="HIGH" if m.confidence > 0.9 else "MEDIUM",
                            confidence=m.confidence,
                            source_type="onion" if ".onion" in page.canonical_url else "surface",
                        )
                        stats["findings"] += 1
                        await self.dwi_client.create_finding({
                            "title": title,
                            "company_id": company.id,
                            "source_url": page.canonical_url,
                        })

            await session.commit()

        logger.info(
            f"[{self.worker_id}] Processed page {page_id}: {stats['entities']} entities, "
            f"{stats['intelligence_records']} intelligence records, {stats['findings']} findings."
        )
        return stats

    async def process_all_pending(self, limit: int = 50) -> int:
        """Processes all pages that have not yet had intelligence extracted."""
        async with self.session_factory() as session:
            # Simple select of recent pages
            stmt = select(Page.id).order_by(Page.last_crawled_at.desc()).limit(limit)
            res = await session.execute(stmt)
            page_ids = list(res.scalars().all())

        processed_count = 0
        for pid in page_ids:
            try:
                await self.process_page(pid)
                processed_count += 1
            except Exception as e:
                logger.error(f"Error processing page {pid}: {e}")

        return processed_count

    async def process_pending_pages(self, limit: int = 50) -> int:
        """Alias for process_all_pending."""
        return await self.process_all_pending(limit=limit)

    async def start_loop(self, poll_interval: float = 5.0) -> None:
        self.is_running = True
        logger.info(f"[{self.worker_id}] Processing worker daemon started.")
        while self.is_running:
            try:
                count = await self.process_all_pending()
                if count == 0:
                    await asyncio.sleep(poll_interval)
            except Exception as e:
                logger.error(f"Error in processing worker loop: {e}")
                await asyncio.sleep(poll_interval)
