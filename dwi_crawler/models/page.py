"""Page, PageVersion, and PageLink models with content-addressable storage references."""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from dwi_crawler.database.session import Base


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    discovered_url_id: Mapped[int] = mapped_column(Integer, ForeignKey("discovered_urls.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)

    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    latest_content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    http_status: Mapped[int] = mapped_column(Integer, default=200)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    content_length: Mapped[int] = mapped_column(Integer, default=0)
    headers_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    redirect_chain_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    retrieved_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    last_crawled_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), index=True)
    version_count: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    discovered_url: Mapped["DiscoveredURL"] = relationship("DiscoveredURL", back_populates="pages")  # type: ignore # noqa: F821
    versions: Mapped[list["PageVersion"]] = relationship("PageVersion", back_populates="page", cascade="all, delete-orphan")
    links: Mapped[list["PageLink"]] = relationship("PageLink", back_populates="source_page", cascade="all, delete-orphan")
    evidence: Mapped[list["Evidence"]] = relationship("Evidence", back_populates="page", cascade="all, delete-orphan")  # type: ignore # noqa: F821


class PageVersion(Base):
    __tablename__ = "page_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page_id: Mapped[int] = mapped_column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, default=1)

    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content_uri: Mapped[str] = mapped_column(Text, nullable=False)
    content_size: Mapped[int] = mapped_column(Integer, default=0)
    mime_type: Mapped[str] = mapped_column(String(100), default="text/html")
    screenshot_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    page: Mapped["Page"] = relationship("Page", back_populates="versions")


class PageLink(Base):
    __tablename__ = "page_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_page_id: Mapped[int] = mapped_column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)

    target_url: Mapped[str] = mapped_column(Text, nullable=False)
    target_canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    target_url_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    link_type: Mapped[str] = mapped_column(String(50), default="a_href")  # a_href, form_action, img_src, script_src, iframe_src, text_url
    is_onion: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    source_page: Mapped["Page"] = relationship("Page", back_populates="links")
