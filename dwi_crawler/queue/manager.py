"""Crawl queue and job manager with exponential backoff, crash recovery, and dead-letter queue."""

import asyncio
from datetime import datetime, timedelta
import json
import logging
from typing import NamedTuple
import uuid
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from dwi_crawler.config.settings import get_settings
from dwi_crawler.models.job import CaptchaEvent, CrawlJob

logger = logging.getLogger("dwi_crawler.queue")


class CrawlJobItem(NamedTuple):
    id: int
    job_id: str
    company_id: int
    discovered_url_id: int
    url: str
    parent_url: str | None
    depth: int
    priority: int
    attempt: int
    max_retries: int


class QueueManager:
    """Manages crawl job lifecycle, queuing, leases, retries, and crash recovery."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()

    async def enqueue_url(
        self,
        discovered_url_id: int,
        company_id: int,
        url: str,
        *,
        parent_url: str | None = None,
        depth: int = 0,
        priority: int = 1,
    ) -> CrawlJob | None:
        """Enqueues a URL for crawling if not already pending or active."""
        # Check if active job exists for this discovered URL
        stmt = select(CrawlJob).where(
            CrawlJob.discovered_url_id == discovered_url_id,
            CrawlJob.status.in_(["PENDING", "RUNNING", "RETRY"]),
        )
        res = await self.session.execute(stmt)
        if res.scalar_one_or_none():
            return None  # Already queued or running

        job = CrawlJob(
            job_id=str(uuid.uuid4()),
            company_id=company_id,
            discovered_url_id=discovered_url_id,
            url=url,
            parent_url=parent_url,
            depth=depth,
            priority=priority,
            attempt=0,
            max_retries=self.settings.max_retries,
            status="PENDING",
            next_run_at=datetime.utcnow(),
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def acquire_next_job(self, worker_id: str) -> CrawlJobItem | None:
        """Atomically acquires the highest priority pending or retry-ready job with lease."""
        now = datetime.utcnow()
        stmt = (
            select(CrawlJob)
            .where(
                CrawlJob.status.in_(["PENDING", "RETRY"]),
                CrawlJob.next_run_at <= now,
            )
            .order_by(CrawlJob.priority.desc(), CrawlJob.depth.asc(), CrawlJob.created_at.asc())
            .limit(1)
        )
        res = await self.session.execute(stmt)
        job = res.scalar_one_or_none()

        if not job:
            return None

        job.status = "RUNNING"
        job.worker_id = worker_id
        job.heartbeat_at = now
        job.attempt += 1
        job.updated_at = now
        await self.session.flush()

        return CrawlJobItem(
            id=job.id,
            job_id=job.job_id,
            company_id=job.company_id,
            discovered_url_id=job.discovered_url_id,
            url=job.url,
            parent_url=job.parent_url,
            depth=job.depth,
            priority=job.priority,
            attempt=job.attempt,
            max_retries=job.max_retries,
        )

    async def update_heartbeat(self, job_id: int) -> None:
        """Extends worker lease on the currently processing job."""
        stmt = update(CrawlJob).where(CrawlJob.id == job_id).values(heartbeat_at=datetime.utcnow())
        await self.session.execute(stmt)
        await self.session.flush()

    async def mark_success(self, job_id: int) -> None:
        stmt = update(CrawlJob).where(CrawlJob.id == job_id).values(
            status="SUCCESS",
            updated_at=datetime.utcnow(),
            error_message=None,
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def mark_failed(self, job_id: int, error_msg: str) -> None:
        """Applies exponential backoff retry or routes to Dead Letter Queue (FAILED)."""
        stmt = select(CrawlJob).where(CrawlJob.id == job_id)
        res = await self.session.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            return

        job.error_message = error_msg[:1000]
        job.updated_at = datetime.utcnow()

        if job.attempt >= job.max_retries:
            job.status = "FAILED"  # Moves to Dead Letter Queue
            logger.error(f"Job {job.job_id} ({job.url}) permanently FAILED after {job.attempt} attempts.")
        else:
            job.status = "RETRY"
            # Exponential backoff: base^attempt seconds (e.g. 5s, 15s, 45s...)
            delay_sec = int(5 * (self.settings.retry_backoff_base ** (job.attempt - 1)))
            job.next_run_at = datetime.utcnow() + timedelta(seconds=delay_sec)
            logger.warning(f"Job {job.job_id} scheduled for RETRY #{job.attempt} in {delay_sec}s.")

        await self.session.flush()

    async def mark_captcha_required(self, job_id: int, url: str, company_id: int, captcha_type: str | None) -> None:
        """Records CAPTCHA requirement without attempting automated bypass."""
        stmt = update(CrawlJob).where(CrawlJob.id == job_id).values(
            status="CAPTCHA_REQUIRED",
            updated_at=datetime.utcnow(),
            error_message=f"CAPTCHA challenge detected: {captcha_type or 'challenge'}",
        )
        await self.session.execute(stmt)

        # Record in captcha_events
        event = CaptchaEvent(
            job_id=job_id,
            company_id=company_id,
            url=url,
            captcha_type=captcha_type or "challenge",
            status="WAITING",
        )
        self.session.add(event)
        await self.session.flush()

    async def recover_stale_jobs(self, timeout_seconds: int = 120) -> int:
        """Recovers crashed jobs where worker heartbeat expired while RUNNING."""
        threshold = datetime.utcnow() - timedelta(seconds=timeout_seconds)
        stmt = select(CrawlJob).where(
            CrawlJob.status == "RUNNING",
            CrawlJob.heartbeat_at < threshold,
        )
        res = await self.session.execute(stmt)
        stale_jobs = res.scalars().all()
        recovered_count = 0

        for job in stale_jobs:
            logger.warning(f"Crash recovery: Job {job.job_id} timed out. Re-queuing for RETRY.")
            job.status = "RETRY"
            job.next_run_at = datetime.utcnow()
            job.error_message = "Worker process died or lost heartbeat."
            recovered_count += 1

        if recovered_count > 0:
            await self.session.flush()
        return recovered_count

    async def retry_failed_jobs(self) -> int:
        """Retries all jobs currently in the dead letter queue (FAILED)."""
        stmt = update(CrawlJob).where(CrawlJob.status == "FAILED").values(
            status="PENDING",
            attempt=0,
            next_run_at=datetime.utcnow(),
            error_message=None,
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.rowcount or 0

    async def list_queue_jobs(self, limit: int = 50, status: str | None = None) -> list[CrawlJob]:
        """Lists crawl jobs from the queue."""
        stmt = select(CrawlJob)
        if status:
            stmt = stmt.where(CrawlJob.status == status)
        stmt = stmt.order_by(CrawlJob.priority.desc(), CrawlJob.created_at.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_queue_stats(self) -> dict[str, int]:
        """Returns aggregate queue counts by status."""
        stmt = select(CrawlJob.status, func.count(CrawlJob.id)).group_by(CrawlJob.status)
        res = await self.session.execute(stmt)
        counts = {k: v for k, v in res.all()}
        return {
            "pending": counts.get("PENDING", 0),
            "running": counts.get("RUNNING", 0),
            "retry": counts.get("RETRY", 0),
            "success": counts.get("SUCCESS", 0),
            "failed": counts.get("FAILED", 0),
            "captcha": counts.get("CAPTCHA_REQUIRED", 0),
            "blocked": counts.get("BLOCKED", 0),
            "skipped": counts.get("SKIPPED", 0),
        }
