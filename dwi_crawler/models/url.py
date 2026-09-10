"""Discovered URLs and URL fingerprint models."""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from dwi_crawler.database.session import Base


class DiscoveredURL(Base):
    __tablename__ = "discovered_urls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    keyword_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("keywords.id", ondelete="SET NULL"), nullable=True, index=True)

    # Full canonical URL without arbitrary truncation
    url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_onion: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    source_type: Mapped[str] = mapped_column(String(50), default="onion")  # surface, onion
    discovered_from: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_query: Mapped[str | None] = mapped_column(Text, nullable=True)

    first_seen: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    # Crawl status: DISCOVERED, QUEUED, CRAWLING, CRAWLED, FAILED, BLOCKED, CAPTCHA_REQUIRED, SKIPPED
    crawl_status: Mapped[str] = mapped_column(String(50), default="DISCOVERED", index=True)
    priority: Mapped[int] = mapped_column(Integer, default=1, index=True)
    depth: Mapped[int] = mapped_column(Integer, default=0, index=True)
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1)  # Tracks repeated discoveries

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="discovered_urls")  # type: ignore # noqa: F821
    pages: Mapped[list["Page"]] = relationship("Page", back_populates="discovered_url", cascade="all, delete-orphan")  # type: ignore # noqa: F821
    crawl_jobs: Mapped[list["CrawlJob"]] = relationship("CrawlJob", back_populates="discovered_url", cascade="all, delete-orphan")  # type: ignore # noqa: F821
