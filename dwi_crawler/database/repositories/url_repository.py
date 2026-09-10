"""Repository for URL storage, deduplication, batch inserts, and querying."""

from datetime import datetime
from urllib.parse import urlparse
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from dwi_crawler.models.url import DiscoveredURL
from dwi_crawler.security.validation import URLNormalizer, is_onion_url


class URLRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_hash(self, url_hash: str) -> DiscoveredURL | None:
        """Retrieves a discovered URL by its canonical SHA256 fingerprint."""
        stmt = select(DiscoveredURL).where(DiscoveredURL.url_hash == url_hash)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def save_or_increment(
        self,
        raw_url: str,
        company_id: int,
        *,
        keyword_id: int | None = None,
        source_type: str = "onion",
        discovered_from: str | None = None,
        search_query: str | None = None,
        priority: int = 1,
        depth: int = 0,
    ) -> tuple[DiscoveredURL, bool]:
        """Normalizes, deduplicates, and saves a URL.
        
        Returns:
            (DiscoveredURL, is_new: bool)
            If the URL already exists, increments occurrence_count, updates last_seen,
            and returns (existing_record, False).
        """
        canonical = URLNormalizer.normalize(raw_url)
        if not canonical:
            raise ValueError(f"Invalid URL: {raw_url}")

        fingerprint = URLNormalizer.fingerprint(canonical)
        existing = await self.get_by_hash(fingerprint)

        if existing:
            existing.occurrence_count += 1
            existing.last_seen = datetime.utcnow()
            # If new depth is shallower, update to shallower depth for queue prioritization
            if depth < existing.depth:
                existing.depth = depth
            await self.session.flush()
            return existing, False

        # Create new record
        parsed = urlparse(canonical)
        domain = (parsed.hostname or "").lower()
        is_onion = is_onion_url(canonical)

        new_record = DiscoveredURL(
            company_id=company_id,
            keyword_id=keyword_id,
            url=raw_url,
            canonical_url=canonical,
            url_hash=fingerprint,
            domain=domain,
            is_onion=is_onion,
            source_type=source_type,
            discovered_from=discovered_from,
            search_query=search_query,
            priority=priority,
            depth=depth,
            crawl_status="DISCOVERED",
            occurrence_count=1,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
        )
        self.session.add(new_record)
        await self.session.flush()
        return new_record, True

    async def bulk_save_or_increment(
        self,
        raw_urls: list[str],
        company_id: int,
        *,
        keyword_id: int | None = None,
        source_type: str = "onion",
        discovered_from: str | None = None,
        depth: int = 1,
    ) -> list[tuple[DiscoveredURL, bool]]:
        """Efficiently processes a batch of URLs with deduplication."""
        results: list[tuple[DiscoveredURL, bool]] = []
        for raw in raw_urls:
            try:
                rec, is_new = await self.save_or_increment(
                    raw_url=raw,
                    company_id=company_id,
                    keyword_id=keyword_id,
                    source_type=source_type,
                    discovered_from=discovered_from,
                    depth=depth,
                )
                results.append((rec, is_new))
            except ValueError:
                continue
        return results

    async def get_queued_urls(
        self,
        company_id: int | None = None,
        limit: int = 50,
        onion_only: bool = True
    ) -> list[DiscoveredURL]:
        """Fetches pending discovered URLs for queuing."""
        stmt = select(DiscoveredURL).where(DiscoveredURL.crawl_status == "DISCOVERED")
        if company_id:
            stmt = stmt.where(DiscoveredURL.company_id == company_id)
        if onion_only:
            stmt = stmt.where(DiscoveredURL.is_onion.is_(True))
        stmt = stmt.order_by(DiscoveredURL.priority.desc(), DiscoveredURL.depth.asc(), DiscoveredURL.first_seen.asc()).limit(limit)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def update_status(self, url_id: int, status: str) -> None:
        """Updates the crawl status of a URL."""
        stmt = update(DiscoveredURL).where(DiscoveredURL.id == url_id).values(crawl_status=status, last_seen=datetime.utcnow())
        await self.session.execute(stmt)
        await self.session.flush()
