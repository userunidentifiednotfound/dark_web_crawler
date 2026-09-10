"""Job, Search Run, Worker Run, CAPTCHA event, and Error tracking models."""

from datetime import datetime
import uuid
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from dwi_crawler.database.session import Base


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    discovered_url_id: Mapped[int] = mapped_column(Integer, ForeignKey("discovered_urls.id", ondelete="CASCADE"), nullable=False, index=True)

    url: Mapped[str] = mapped_column(Text, nullable=False)
    parent_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    depth: Mapped[int] = mapped_column(Integer, default=0, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=1, index=True)
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=4)

    # Status: PENDING, RUNNING, SUCCESS, FAILED, RETRY, BLOCKED, CAPTCHA_REQUIRED, SKIPPED
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now(), index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    discovered_url: Mapped["DiscoveredURL"] = relationship("DiscoveredURL", back_populates="crawl_jobs")  # type: ignore # noqa: F821


class SearchRun(Base):
    __tablename__ = "search_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    keyword_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("keywords.id", ondelete="SET NULL"), nullable=True, index=True)

    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="onion")  # surface, onion
    results_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="SUCCESS")  # SUCCESS, FAILED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    results: Mapped[list["SearchResult"]] = relationship("SearchResult", back_populates="search_run", cascade="all, delete-orphan")


class SearchResult(Base):
    __tablename__ = "search_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    search_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("search_runs.id", ondelete="CASCADE"), nullable=False, index=True)

    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), default="onion")
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    search_run: Mapped["SearchRun"] = relationship("SearchRun", back_populates="results")


class CaptchaEvent(Base):
    __tablename__ = "captcha_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("crawl_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    captcha_type: Mapped[str] = mapped_column(String(50), default="turnstile_or_image")

    detected_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    status: Mapped[str] = mapped_column(String(50), default="WAITING", index=True)  # WAITING, HUMAN_RESOLVED, FAILED, EXPIRED
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)


class WorkerRun(Base):
    __tablename__ = "worker_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    worker_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    worker_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # discovery, crawler, browser, processor
    status: Mapped[str] = mapped_column(String(50), default="RUNNING", index=True)  # RUNNING, STOPPED, FAILED
    started_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    heartbeat_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), index=True)
    jobs_processed: Mapped[int] = mapped_column(Integer, default=0)


class CrawlerError(Base):
    __tablename__ = "crawler_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    error_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
