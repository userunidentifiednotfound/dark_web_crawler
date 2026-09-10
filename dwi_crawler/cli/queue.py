"""CLI commands for managing the crawl queue and dead-letter queue."""

import asyncio
import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import select
from dwi_crawler.database.session import get_async_session_factory, init_db
from dwi_crawler.models.job import CrawlJob
from dwi_crawler.queue.manager import QueueManager

queue_app = typer.Typer(name="queue", help="Manage crawl queue, dead-letter jobs, and retry policies.")
console = Console()


@queue_app.command("status")
def queue_status():
    """Display real-time queue counts and pipeline statuses."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            mgr = QueueManager(session)
            stats = await mgr.get_queue_stats()

            table = Table(title="DWI Crawl Queue Status")
            table.add_column("Queue State", style="bold white")
            table.add_column("Count", justify="right", style="bold cyan")

            status_colors = {
                "pending": "yellow",
                "running": "blue",
                "retry": "magenta",
                "success": "green",
                "failed": "red",
                "captcha": "bright_red",
                "blocked": "dim",
                "skipped": "dim",
            }

            for st, count in stats.items():
                color = status_colors.get(st, "white")
                table.add_row(f"[{color}]{st.upper()}[/{color}]", str(count))

            console.print(table)
    asyncio.run(_run())


@queue_app.command("failed")
def list_failed(limit: int = typer.Option(20, "--limit", "-l", help="Number of failed jobs to show")):
    """List permanently failed jobs currently in the Dead Letter Queue."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            stmt = select(CrawlJob).where(CrawlJob.status == "FAILED").order_by(CrawlJob.updated_at.desc()).limit(limit)
            res = await session.execute(stmt)
            failed_jobs = list(res.scalars().all())

            if not failed_jobs:
                console.print("[bold green]✓ Dead Letter Queue is empty. No failed jobs.[/bold green]")
                return

            table = Table(title=f"Dead Letter Queue (Failed Jobs, showing {len(failed_jobs)})")
            table.add_column("Job ID", style="cyan")
            table.add_column("URL", style="bold red")
            table.add_column("Attempts", justify="right", style="yellow")
            table.add_column("Error Reason", style="dim")
            table.add_column("Failed At", style="magenta")

            for j in failed_jobs:
                table.add_row(
                    j.job_id[:8],
                    j.url,
                    str(j.attempt),
                    (j.error_message or "Unknown")[:45],
                    j.updated_at.strftime("%Y-%m-%d %H:%M"),
                )
            console.print(table)
    asyncio.run(_run())


@queue_app.command("retry")
def retry_jobs(failed_only: bool = typer.Option(True, "--failed/--all", help="Retry dead-letter failed jobs")):
    """Requeue dead-letter or stalled jobs back into active processing."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            mgr = QueueManager(session)
            count = await mgr.retry_failed_jobs()
            await session.commit()
            console.print(f"[bold green]✓ Re-queued {count} dead-letter jobs back to PENDING state.[/bold green]")
    asyncio.run(_run())
