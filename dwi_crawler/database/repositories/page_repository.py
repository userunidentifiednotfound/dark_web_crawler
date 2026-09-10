"""Repository for pages, versioning, links, and content deduplication."""

from datetime import datetime
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from dwi_crawler.models.page import Page, PageLink, PageVersion
from dwi_crawler.processing.links import ExtractedLink
from dwi_crawler.storage.content import get_content_storage


class PageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.cas = get_content_storage()

    async def save_page_fetch(
        self,
        discovered_url_id: int,
        company_id: int,
        canonical_url: str,
        url_hash: str,
        raw_bytes: bytes,
        mime_type: str,
        http_status: int,
        headers_dict: dict[str, str],
        final_url: str,
        redirect_chain: list[str],
        *,
        screenshot_bytes: bytes | None = None,
    ) -> tuple[Page, PageVersion, bool]:
        """Saves page fetch results with CAS and version tracking.
        
        Returns:
            (Page, PageVersion, is_new_content: bool)
        """
        import json

        # 1. Store in Content-Addressable Storage (CAS)
        content_hash, content_uri, content_size = self.cas.store_content(raw_bytes, mime_type=mime_type)

        screenshot_uri = None
        if screenshot_bytes:
            s_hash, s_uri, _ = self.cas.store_content(screenshot_bytes, mime_type="image/png")
            screenshot_uri = s_uri

        # 2. Check if a Page record already exists for this URL
        stmt = select(Page).where(Page.url_hash == url_hash).options(selectinload(Page.versions))
        res = await self.session.execute(stmt)
        page = res.scalar_one_or_none()

        now = datetime.utcnow()
        headers_str = json.dumps(headers_dict)
        redirects_str = json.dumps(redirect_chain)

        if not page:
            # Create new page record
            page = Page(
                discovered_url_id=discovered_url_id,
                company_id=company_id,
                canonical_url=canonical_url,
                url_hash=url_hash,
                latest_content_hash=content_hash,
                http_status=http_status,
                content_type=mime_type,
                content_length=content_size,
                headers_json=headers_str,
                final_url=final_url,
                redirect_chain_json=redirects_str,
                retrieved_at=now,
                last_crawled_at=now,
                version_count=1,
            )
            self.session.add(page)
            await self.session.flush()

            version = PageVersion(
                page_id=page.id,
                version_number=1,
                content_hash=content_hash,
                content_uri=content_uri,
                content_size=content_size,
                mime_type=mime_type,
                screenshot_uri=screenshot_uri,
                retrieved_at=now,
            )
            self.session.add(version)
            await self.session.flush()
            return page, version, True

        # Existing page: check if content hash changed
        page.last_crawled_at = now
        page.http_status = http_status
        page.content_type = mime_type
        page.content_length = content_size
        page.headers_json = headers_str
        page.final_url = final_url
        page.redirect_chain_json = redirects_str

        if page.latest_content_hash == content_hash:
            # Duplicate content: retrieve existing version without creating duplicate version row
            ver_stmt = select(PageVersion).where(
                PageVersion.page_id == page.id,
                PageVersion.content_hash == content_hash
            )
            v_res = await self.session.execute(ver_stmt)
            latest_version = v_res.scalar_one_or_none()
            if not latest_version:
                latest_version = page.versions[-1]
            await self.session.flush()
            return page, latest_version, False

        # Content changed: increment version count and add new PageVersion
        page.version_count += 1
        page.latest_content_hash = content_hash

        new_version = PageVersion(
            page_id=page.id,
            version_number=page.version_count,
            content_hash=content_hash,
            content_uri=content_uri,
            content_size=content_size,
            mime_type=mime_type,
            screenshot_uri=screenshot_uri,
            retrieved_at=now,
        )
        self.session.add(new_version)
        await self.session.flush()
        return page, new_version, True

    async def save_extracted_links(
        self,
        page_id: int,
        links: list[ExtractedLink],
    ) -> list[PageLink]:
        """Saves discovered links attached to the source page."""
        saved_links: list[PageLink] = []
        for lk in links:
            pl = PageLink(
                source_page_id=page_id,
                target_url=lk.raw_url,
                target_canonical_url=lk.canonical_url,
                target_url_hash=lk.url_hash,
                link_type=lk.link_type,
                is_onion=lk.is_onion,
            )
            self.session.add(pl)
            saved_links.append(pl)
        await self.session.flush()
        return saved_links

    async def get_page(self, page_id: int) -> Page | None:
        stmt = select(Page).where(Page.id == page_id).options(selectinload(Page.versions))
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_pages(self, company_id: int | None = None, limit: int | None = None) -> list[Page]:
        stmt = select(Page)
        if company_id:
            stmt = stmt.where(Page.company_id == company_id)
        stmt = stmt.order_by(Page.last_crawled_at.desc())
        if limit is not None:
            stmt = stmt.limit(limit)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def list_links(self, page_id: int | None = None, limit: int = 100) -> list[PageLink]:
        stmt = select(PageLink)
        if page_id:
            stmt = stmt.where(PageLink.source_page_id == page_id)
        stmt = stmt.order_by(PageLink.created_at.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
